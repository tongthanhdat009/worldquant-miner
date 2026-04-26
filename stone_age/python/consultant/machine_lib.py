import requests
from os import environ
from time import sleep
import time
import json
import pandas as pd
import random
import pickle
import re
import math
from itertools import product
from itertools import combinations
from collections import defaultdict
import pickle
import logging
import csv

arsenal = ["ts_moment", "ts_entropy", "ts_min_max_cps", "ts_min_max_diff", "inst_tvr", 'sigmoid', 
           "ts_decay_exp_window", "ts_percentage", "vector_neut", "vector_proj", "signed_power"]

group_ops = ["group_rank", "group_sum", "group_max", "group_mean", "group_median", "group_min", "group_std_dev"]

twin_field_ops = ["ts_corr", "ts_covariance", "ts_co_kurtosis", "ts_co_skewness", "ts_theilsen"]

default_blocked_ops = {
    "fraction",
    "log_diff",
    "s_log_1p",
    "scale_down",
    "ts_ir",
    "ts_min_diff",
    "vec_choose",
}

class WorldQuantBrain:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = None
        self.blocked_ops = self._load_blocked_ops()
        self.pass_hunting_mode = environ.get("PASS_HUNTING_MODE", "1") != "0"
        self.safe_vector_ops = self._load_safe_vector_ops()
        self.default_truncation = self._read_float_env("ALPHA_TRUNCATION", 0.05)
        self.default_neutralization = self._normalize_neutralization(
            environ.get(
                "DEFAULT_NEUTRALIZATION",
                "SUBINDUSTRY" if self.pass_hunting_mode else "INDUSTRY",
            )
        )
        self.max_matrix_fields = max(1, self._read_int_env("MAX_MATRIX_FIELDS", 24))
        self.max_vector_fields = max(1, self._read_int_env("MAX_VECTOR_FIELDS", 16))
        self.max_candidates_per_field = max(1, self._read_int_env("MAX_CANDIDATES_PER_FIELD", 14))
        self.history_profile_path = environ.get("TESTED_ALPHAS_PATH", "tested_alphas.json")
        self.history_learning_output_path = environ.get(
            "HISTORY_LEARNING_OUTPUT_PATH",
            "history_learning_profile.json",
        )
        self.field_history_scores = {}
        self.field_history_stats = {}
        self.operator_history_scores = {}
        self.operator_history_stats = {}
        self.history_learning_summary = {}
        self.basic_ops = ["log", "sqrt", "reverse", "inverse", "rank", "zscore", "quantile", "normalize"]
        self.ts_ops = [
            "ts_rank",
            "ts_zscore",
            "ts_delta",
            "ts_sum",
            "ts_product",
            "ts_std_dev",
            "ts_mean",
            "ts_arg_min",
            "ts_arg_max",
        ]
        self.experimental_ops = [
            "log_diff",
            "s_log_1p",
            "fraction",
            "scale_down",
            "ts_ir",
            "ts_min_diff",
            "ts_max_diff",
            "ts_returns",
            "ts_scale",
            "ts_skewness",
            "ts_kurtosis",
            "ts_quantile",
        ] + arsenal + group_ops
        ops = self.basic_ops + self.ts_ops
        if environ.get("ENABLE_EXPERIMENTAL_OPERATORS", "0") == "1":
            ops += self.experimental_ops
        else:
            logging.info("Experimental operators disabled; set ENABLE_EXPERIMENTAL_OPERATORS=1 to include them")
        self.ops_set = self._filter_blocked_ops(ops)
        self._load_history_learning_profile()
        self.ops_set = self._filter_blocked_ops(self.ops_set)
        self.safe_vector_ops = [op for op in self.safe_vector_ops if op not in self.blocked_ops]
        self.login()

    @staticmethod
    def _read_int_env(name, default):
        value = environ.get(name)
        if value in (None, ""):
            return default
        try:
            return int(value)
        except ValueError:
            logging.warning("Invalid integer for %s=%s. Falling back to %s", name, value, default)
            return default

    @staticmethod
    def _read_float_env(name, default):
        value = environ.get(name)
        if value in (None, ""):
            return default
        try:
            return float(value)
        except ValueError:
            logging.warning("Invalid float for %s=%s. Falling back to %s", name, value, default)
            return default

    @staticmethod
    def _normalize_neutralization(value):
        value = str(value or "INDUSTRY").upper()
        allowed = {"NONE", "MARKET", "SECTOR", "INDUSTRY", "SUBINDUSTRY"}
        if value not in allowed:
            logging.warning("Unknown neutralization %s. Falling back to INDUSTRY", value)
            return "INDUSTRY"
        return value

    def _load_safe_vector_ops(self):
        if self.pass_hunting_mode:
            default_value = "vec_avg,vec_sum,vec_max,vec_stddev,vec_skewness,vec_ir"
        else:
            default_value = "vec_avg,vec_sum,vec_ir,vec_max,vec_count,vec_skewness,vec_stddev"

        configured = environ.get("SAFE_VECTOR_OPERATORS", default_value)
        ops = []
        for op in configured.split(","):
            op = op.strip()
            if not op:
                continue
            if op in self.blocked_ops:
                logging.info("Skipping blocked vector operator during generation: %s", op)
                continue
            ops.append(op)

        if not ops:
            ops = ["vec_avg", "vec_sum", "vec_max"]
        return ops

    @staticmethod
    def _safe_float(value, default=0.0):
        try:
            if value in (None, ""):
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _new_history_stat():
        return {
            "count": 0,
            "checked_count": 0,
            "score_sum": 0.0,
            "best_score": -999.0,
            "best_sharpe": -999.0,
            "best_fitness": -999.0,
            "fail_counts": defaultdict(int),
            "simulation_error_count": 0,
            "near_pass_count": 0,
        }

    def _load_history_learning_profile(self):
        records = []
        try:
            with open(self.history_profile_path, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, list):
                records = loaded
        except FileNotFoundError:
            logging.info("History learning skipped because %s was not found", self.history_profile_path)
            return
        except json.JSONDecodeError as exc:
            logging.warning("History learning skipped because %s could not be parsed: %s", self.history_profile_path, exc)
            return

        if not records:
            logging.info("History learning skipped because %s is empty", self.history_profile_path)
            return

        field_stats = defaultdict(self._new_history_stat)
        operator_stats = defaultdict(self._new_history_stat)

        for record in records:
            if not isinstance(record, dict):
                continue

            code = str(record.get("code") or "").strip()
            if not code:
                continue

            quality = self._score_history_record(record)
            failed_names = self._history_failed_names(record)
            operators = self._extract_expression_operators(code)
            fields = self._extract_expression_fields(code)
            simulation_status = str(record.get("simulation_status") or "")
            blocked_operator = self._extract_blocked_operator_from_record(record)
            if simulation_status == "SKIPPED_INACCESSIBLE_OPERATOR" and not blocked_operator:
                blocked_operator = self._first_blocked_operator(code)
            field_quality = self._score_history_record(record, ignore_access_failures=True)

            for operator_name in operators:
                if simulation_status == "SKIPPED_INACCESSIBLE_OPERATOR":
                    if not blocked_operator or operator_name != blocked_operator:
                        continue
                    operator_quality = -2.0
                    operator_failed_names = ["SKIPPED_INACCESSIBLE_OPERATOR"]
                else:
                    operator_quality = quality
                    operator_failed_names = failed_names

                self._update_history_stat(
                    operator_stats[operator_name],
                    record,
                    operator_quality,
                    operator_failed_names,
                )

            if simulation_status == "COMPLETE":
                for field_name in fields:
                    self._update_history_stat(
                        field_stats[field_name],
                        record,
                        field_quality,
                        failed_names,
                    )

        self.field_history_stats = self._finalize_history_stats(field_stats)
        self.field_history_scores = {
            name: stats["history_score"]
            for name, stats in self.field_history_stats.items()
        }
        self.operator_history_stats = self._finalize_history_stats(operator_stats)
        self.operator_history_scores = {
            name: stats["history_score"]
            for name, stats in self.operator_history_stats.items()
        }
        learned_blocked_ops = [
            name
            for name, stats in self.operator_history_stats.items()
            if stats.get("count", 0) >= 3 and stats.get("inaccessible_rate", 0.0) >= 0.5
        ]
        for operator_name in learned_blocked_ops:
            if operator_name not in self.blocked_ops:
                self.blocked_ops.add(operator_name)

        self.history_learning_summary = self._build_history_learning_summary(records)
        self._save_history_learning_summary()

        logging.info(
            "Loaded history learning profile from %s: %s fields, %s operators, %s learned blocked ops",
            self.history_profile_path,
            len(self.field_history_scores),
            len(self.operator_history_scores),
            len(learned_blocked_ops),
        )

    def _extract_blocked_operator_from_record(self, record):
        if not isinstance(record, dict):
            return None

        for value in (
            record.get("simulation_error"),
            record.get("simulation_payload"),
        ):
            blocked_operator = self._extract_inaccessible_operator(value)
            if blocked_operator:
                return blocked_operator

        return None

    def _score_history_record(self, record, ignore_access_failures=False):
        failed_names = self._history_failed_names(record)
        simulation_status = str(record.get("simulation_status") or "")
        check_status = str(record.get("check_status") or "")
        sharpe = self._safe_float(record.get("sharpe"))
        fitness = self._safe_float(record.get("fitness"))
        turnover = self._safe_float(record.get("turnover"))
        margin = self._safe_float(record.get("margin"))

        blocking_statuses = {
            "ERROR",
            "FAILED",
            "FAIL",
            "INVALID",
            "MONITOR_ERROR",
            "PROGRESS_RESPONSE_ERROR",
        }
        if not ignore_access_failures:
            blocking_statuses = blocking_statuses | {"SKIPPED_INACCESSIBLE_OPERATOR"}

        if simulation_status in blocking_statuses or check_status == "simulation_error":
            return -2.0

        quality = 0.0
        quality += min(max(sharpe, -1.25), 1.5) / 1.25
        quality += min(max(fitness, -1.0), 1.25) / 1.0
        quality += min(max(margin, -0.02), 0.02) * 8.0

        if 0.02 <= turnover <= 0.6:
            quality += 0.2
        elif turnover < 0.01:
            quality -= 0.2
        elif turnover > 0.7:
            quality -= 0.4

        if record.get("passed") is True:
            quality += 2.0

        fail_penalties = {
            "LOW_SHARPE": 0.8,
            "LOW_FITNESS": 0.8,
            "LOW_SUB_UNIVERSE_SHARPE": 0.45,
            "CONCENTRATED_WEIGHT": 0.45,
            "HIGH_TURNOVER": 0.4,
            "LOW_TURNOVER": 0.2,
            "SKIPPED_INACCESSIBLE_OPERATOR": 1.5,
            "ERROR": 1.0,
        }
        for failed_name in failed_names:
            if ignore_access_failures and failed_name == "SKIPPED_INACCESSIBLE_OPERATOR":
                continue
            quality -= fail_penalties.get(failed_name, 0.1)

        return quality

    @staticmethod
    def _history_failed_names(record):
        names = record.get("failed_check_names") or []
        if isinstance(names, str):
            names = [part.strip() for part in names.split(";") if part.strip()]

        simulation_status = str(record.get("simulation_status") or "")
        if simulation_status and simulation_status not in {"COMPLETE", "UNKNOWN"}:
            names = list(names) + [simulation_status]

        return [str(name) for name in names if str(name)]

    def _update_history_stat(self, stat, record, quality, failed_names):
        stat["count"] += 1
        stat["score_sum"] += quality
        stat["best_score"] = max(stat["best_score"], quality)
        stat["best_sharpe"] = max(stat["best_sharpe"], self._safe_float(record.get("sharpe"), -999.0))
        stat["best_fitness"] = max(stat["best_fitness"], self._safe_float(record.get("fitness"), -999.0))

        if str(record.get("simulation_status") or "") == "COMPLETE":
            stat["checked_count"] += 1
        else:
            stat["simulation_error_count"] += 1

        if self._is_near_pass_record(record):
            stat["near_pass_count"] += 1

        for failed_name in failed_names:
            stat["fail_counts"][failed_name] += 1

    def _is_near_pass_record(self, record):
        if str(record.get("simulation_status") or "") != "COMPLETE":
            return False

        sharpe = self._safe_float(record.get("sharpe"))
        fitness = self._safe_float(record.get("fitness"))
        failed_names = set(self._history_failed_names(record))
        blocked = {
            "SKIPPED_INACCESSIBLE_OPERATOR",
            "ERROR",
            "CONCENTRATED_WEIGHT",
            "HIGH_TURNOVER",
        }
        if failed_names & blocked:
            return False
        return sharpe >= 0.9 or fitness >= 0.6

    def _finalize_history_stats(self, stats_map):
        finalized = {}
        for name, stat in stats_map.items():
            count = stat["count"]
            if count <= 0:
                continue

            checked_count = max(1, stat["checked_count"])
            mean_score = stat["score_sum"] / count
            near_pass_rate = stat["near_pass_count"] / count
            inaccessible_rate = stat["fail_counts"].get("SKIPPED_INACCESSIBLE_OPERATOR", 0) / count
            sub_universe_rate = stat["fail_counts"].get("LOW_SUB_UNIVERSE_SHARPE", 0) / checked_count
            concentration_rate = stat["fail_counts"].get("CONCENTRATED_WEIGHT", 0) / checked_count
            high_turnover_rate = stat["fail_counts"].get("HIGH_TURNOVER", 0) / checked_count

            history_score = mean_score
            history_score += max(0.0, min(1.5, stat["best_score"])) * 0.35
            history_score += near_pass_rate * 0.8
            history_score -= inaccessible_rate * 1.5
            history_score -= sub_universe_rate * 0.55
            history_score -= concentration_rate * 0.45
            history_score -= high_turnover_rate * 0.35

            finalized[name] = {
                "count": count,
                "checked_count": stat["checked_count"],
                "mean_score": mean_score,
                "best_score": stat["best_score"],
                "best_sharpe": None if stat["best_sharpe"] <= -900 else stat["best_sharpe"],
                "best_fitness": None if stat["best_fitness"] <= -900 else stat["best_fitness"],
                "near_pass_rate": near_pass_rate,
                "inaccessible_rate": inaccessible_rate,
                "sub_universe_rate": sub_universe_rate,
                "concentration_rate": concentration_rate,
                "high_turnover_rate": high_turnover_rate,
                "history_score": history_score,
                "fail_counts": dict(stat["fail_counts"]),
            }

        return finalized

    def _build_history_learning_summary(self, records):
        top_fields = self._top_history_entities(self.field_history_stats)
        top_operators = self._top_history_entities(self.operator_history_stats)
        risky_fields = self._top_history_entities(self.field_history_stats, reverse=False)
        risky_operators = self._top_history_entities(self.operator_history_stats, reverse=False)

        return {
            "source_path": self.history_profile_path,
            "record_count": len(records),
            "top_fields": top_fields[:15],
            "top_operators": top_operators[:15],
            "risky_fields": risky_fields[:15],
            "risky_operators": risky_operators[:15],
        }

    @staticmethod
    def _top_history_entities(stats_map, reverse=True):
        ordered = sorted(
            stats_map.items(),
            key=lambda item: (item[1].get("history_score", 0.0), item[1].get("count", 0)),
            reverse=reverse,
        )
        results = []
        for name, stats in ordered:
            results.append({
                "name": name,
                "history_score": round(stats.get("history_score", 0.0), 4),
                "count": stats.get("count", 0),
                "best_sharpe": stats.get("best_sharpe"),
                "best_fitness": stats.get("best_fitness"),
                "near_pass_rate": round(stats.get("near_pass_rate", 0.0), 4),
                "sub_universe_rate": round(stats.get("sub_universe_rate", 0.0), 4),
                "concentration_rate": round(stats.get("concentration_rate", 0.0), 4),
                "high_turnover_rate": round(stats.get("high_turnover_rate", 0.0), 4),
                "inaccessible_rate": round(stats.get("inaccessible_rate", 0.0), 4),
            })
        return results

    def _save_history_learning_summary(self):
        if not self.history_learning_summary:
            return
        try:
            with open(self.history_learning_output_path, "w", encoding="utf-8") as handle:
                json.dump(self.history_learning_summary, handle, indent=2)
        except OSError as exc:
            logging.warning(
                "Could not write history learning summary to %s: %s",
                self.history_learning_output_path,
                exc,
            )

    def _expression_function_names(self):
        function_names = set(self.basic_ops)
        function_names.update(self.ts_ops)
        function_names.update(self.experimental_ops)
        function_names.update(arsenal)
        function_names.update(group_ops)
        function_names.update(twin_field_ops)
        function_names.update({
            "winsorize",
            "ts_backfill",
            "bucket",
            "densify",
            "scale",
            "group_neutralize",
            "group_zscore",
            "group_rank",
            "group_scale",
            "group_sum",
            "group_max",
            "group_mean",
            "group_median",
            "group_min",
            "group_std_dev",
            "trade_when",
            "if_else",
            "abs",
            "sign",
            "max",
            "min",
        })
        return function_names

    def _extract_expression_operators(self, code):
        function_names = set(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", str(code or "")))
        return sorted(name for name in function_names if name in self._expression_function_names())

    def _extract_expression_fields(self, code):
        text = str(code or "")
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)
        function_names = set(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", text))
        excluded_tokens = self._expression_function_names() | {
            "market",
            "sector",
            "industry",
            "subindustry",
            "std",
            "percentage",
            "factor",
            "buckets",
            "range",
            "lag",
            "rettype",
            "constant",
            "nth",
            "longscale",
            "shortscale",
            "scale",
            "true",
            "false",
        }

        fields = []
        seen = set()
        for token in tokens:
            if token in function_names or token in excluded_tokens:
                continue
            if token in seen:
                continue
            seen.add(token)
            fields.append(token)
        return fields

    def _history_expression_score(self, code):
        fields = self._extract_expression_fields(code)
        operators = self._extract_expression_operators(code)
        score = 0.0

        if fields:
            score += sum(self.field_history_scores.get(field, 0.0) for field in fields) / len(fields) * 1.2
        if operators:
            score += sum(self.operator_history_scores.get(operator, 0.0) for operator in operators) / len(operators) * 0.8
        return score

    def _load_blocked_ops(self):
        blocked_ops = set(default_blocked_ops)
        extra_ops = environ.get("BLOCKED_OPERATORS", "")
        for op in extra_ops.split(","):
            op = op.strip()
            if op:
                blocked_ops.add(op)
        return blocked_ops

    def _filter_blocked_ops(self, ops):
        filtered_ops = []
        for op in ops:
            if op in self.blocked_ops:
                logging.info("Skipping blocked operator during generation: %s", op)
                continue
            filtered_ops.append(op)
        return filtered_ops

    def login(self):
        """Initialize or refresh session with WorldQuant Brain."""
        logging.info("Authenticating with WorldQuant Brain...")
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        response = self.session.post('https://api.worldquantbrain.com/authentication')
        
        if response.status_code != 201:
            raise Exception(f"Authentication failed: {response.text}")
            
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        logging.info("Authentication successful")
        return self.session

    def multi_simulate(
        self,
        alpha_pools: list,
        neut: str,
        region: str,
        universe: str,
        start: int = 0,
        deadline=None,
    ):
        """Run multiple alpha simulations in parallel."""
        logging.info(f"Starting multi-simulate for {len(alpha_pools)} pools")
        completed_alphas = []
        
        for x, pool in enumerate(alpha_pools):
            if x < start:
                continue
            if self._deadline_reached(deadline):
                logging.info("Run duration reached; stopping before next pool")
                break
                
            progress_items = []
            logging.info(f"Processing pool {x+1}/{len(alpha_pools)}")
            should_stop = False
            
            for y, task in enumerate(pool):
                if self._deadline_reached(deadline):
                    logging.info("Run duration reached; stopping before next task")
                    should_stop = True
                    break
                
                sim_data_list = self.generate_sim_data(task, region, universe, neut)
                logging.info(f"Generated simulation data for task {y+1}/{len(pool)}")
                
                for sim_index, sim_data in enumerate(sim_data_list, 1):
                    if self._deadline_reached(deadline):
                        logging.info("Run duration reached; stopping before posting next simulation")
                        should_stop = True
                        break
                    
                    alpha_code = sim_data.get("regular", "")
                    blocked_op = self._first_blocked_operator(alpha_code)
                    if blocked_op:
                        logging.info(
                            "Skipping alpha with blocked operator %s: %s",
                            blocked_op,
                            alpha_code,
                        )
                        completed_alphas.append(
                            self._build_simulation_result(
                                alpha_code,
                                sim_data.get("settings", {}),
                                "SKIPPED_INACCESSIBLE_OPERATOR",
                                "",
                                {
                                    "message": f"Operator is blocked for this account/API: {blocked_op}",
                                    "operator": blocked_op,
                                },
                            )
                        )
                        continue
                     
                    try:
                        simulation_response = self.session.post(
                            'https://api.worldquantbrain.com/simulations',
                            json=sim_data,
                        )
                        if simulation_response.status_code == 401:
                            logging.info("Session expired, re-authenticating...")
                            self.login()
                            simulation_response = self.session.post(
                                'https://api.worldquantbrain.com/simulations',
                                json=sim_data,
                            )
                        
                        if simulation_response.status_code != 201:
                            logging.error(f"Simulation API error: {simulation_response.text}")
                            continue
                            
                        simulation_progress_url = simulation_response.headers.get('Location')
                        if not simulation_progress_url:
                            logging.error("No Location header in response")
                            continue
                            
                        progress_items.append({
                            "url": simulation_progress_url,
                            "code": sim_data.get("regular", ""),
                            "settings": sim_data.get("settings", {}),
                            "pool": x + 1,
                            "task": y + 1,
                            "simulation": sim_index,
                        })
                        logging.info(
                            f"Posted simulation for task {y+1}.{sim_index}, "
                            f"got progress URL: {simulation_progress_url}"
                        )
                        
                    except Exception as e:
                        logging.error(f"Error posting simulation: {str(e)}")
                        sleep_seconds = self._sleep_seconds_before_retry(deadline, 600)
                        if sleep_seconds <= 0:
                            logging.info("Run duration reached while waiting to retry simulation post")
                            should_stop = True
                            break
                        
                        sleep(sleep_seconds)
                        if self._deadline_reached(deadline):
                            logging.info("Run duration reached while waiting to retry simulation post")
                            should_stop = True
                            break
                        
                        self.login()
                        continue

            completed_alphas.extend(self._monitor_progress(progress_items))
            logging.info(f"Pool {x+1} simulations completed")
            
            if should_stop or self._deadline_reached(deadline):
                logging.info("Run duration reached; stopping after current pool")
                break
        
        return completed_alphas

    @staticmethod
    def _deadline_reached(deadline):
        return deadline is not None and time.monotonic() >= deadline

    @staticmethod
    def _sleep_seconds_before_retry(deadline, default_seconds):
        if deadline is None:
            return default_seconds
        return min(default_seconds, max(0, deadline - time.monotonic()))

    def _monitor_progress(self, progress_items: list):
        """Monitor simulation progress."""
        simulation_results = []
        for j, item in enumerate(progress_items):
            if isinstance(item, dict):
                progress = item.get("url")
                code = item.get("code", "")
                settings = item.get("settings", {}) or {}
            else:
                progress = item
                code = ""
                settings = {}
            
            if not progress:
                logging.warning("Skipping simulation progress item without URL: %s", item)
                continue
            
            try:
                while True:
                    simulation_progress = self.session.get(progress)
                    if simulation_progress.status_code == 401:
                        logging.info("Session expired while monitoring progress, re-authenticating...")
                        self.login()
                        simulation_progress = self.session.get(progress)
                    retry_after = simulation_progress.headers.get("Retry-After", 0)
                    if not retry_after:
                        break
                    sleep(float(retry_after))

                try:
                    progress_payload = simulation_progress.json()
                except ValueError:
                    error_text = simulation_progress.text[:500]
                    logging.warning(
                        "Simulation progress returned non-JSON response for task %s: "
                        "status=%s, body=%s, alpha=%s",
                        j + 1,
                        simulation_progress.status_code,
                        error_text,
                        code,
                    )
                    simulation_results.append(
                        self._build_simulation_result(
                            code,
                            settings,
                            "PROGRESS_RESPONSE_ERROR",
                            progress,
                            {"http_status": simulation_progress.status_code, "body": error_text},
                        )
                    )
                    continue
                
                status = progress_payload.get("status")
                logging.info(f"Task {j+1} status: {status}")
                if status != "COMPLETE":
                    blocked_op = self._extract_inaccessible_operator(progress_payload)
                    if blocked_op:
                        self.blocked_ops.add(blocked_op)
                        logging.warning(
                            "Learned inaccessible operator from API and will skip it: %s",
                            blocked_op,
                        )
                    logging.warning(
                        "Task not complete: %s | alpha=%s | payload=%s",
                        progress,
                        code,
                        self._compact_payload(progress_payload),
                    )
                    simulation_results.append(
                        self._build_simulation_result(
                            code,
                            settings,
                            status or "UNKNOWN",
                            progress,
                            progress_payload,
                        )
                    )
                    continue
                
                alpha_ids = self._extract_alpha_ids(progress_payload)
                if not alpha_ids:
                    logging.warning(f"Completed simulation but no alpha id found: {progress_payload}")
                    simulation_results.append(
                        self._build_simulation_result(
                            code,
                            settings,
                            "COMPLETE_NO_ALPHA_ID",
                            progress,
                            progress_payload,
                        )
                    )
                    continue
                
                for alpha_id in alpha_ids:
                    result = self._build_simulation_result(
                        code,
                        settings,
                        status,
                        progress,
                        progress_payload,
                    )
                    result.update({
                        "alpha_id": alpha_id,
                    })
                    simulation_results.append(result)
                    logging.info(f"Completed alpha: {alpha_id}")

            except Exception as e:
                logging.error(f"Error monitoring progress: {str(e)}")
                simulation_results.append(
                    self._build_simulation_result(
                        code,
                        settings,
                        "MONITOR_ERROR",
                        progress,
                        {"error": str(e)},
                    )
                )
        return simulation_results

    @staticmethod
    def _build_simulation_result(code, settings, status, progress_url, payload):
        settings = settings or {}
        return {
            "alpha_id": "",
            "code": code,
            "region": settings.get("region"),
            "universe": settings.get("universe"),
            "delay": settings.get("delay"),
            "decay": settings.get("decay"),
            "neutralization": settings.get("neutralization"),
            "truncation": settings.get("truncation"),
            "simulation_status": status,
            "progress_url": progress_url,
            "simulation_error": WorldQuantBrain._extract_simulation_error(payload),
            "simulation_payload": payload,
        }

    @staticmethod
    def _extract_simulation_error(payload):
        if not isinstance(payload, dict):
            return str(payload)[:500]
        
        for key in ("message", "error", "detail", "reason"):
            value = payload.get(key)
            if value:
                return str(value)[:500]
        
        for key in ("errors", "warnings", "checks"):
            value = payload.get(key)
            if value:
                return WorldQuantBrain._compact_payload(value, limit=500)
        
        return WorldQuantBrain._compact_payload(payload, limit=500)

    def _first_blocked_operator(self, code):
        code = str(code or "")
        for op in sorted(self.blocked_ops, key=len, reverse=True):
            if re.search(r"(?<![A-Za-z0-9_])" + re.escape(op) + r"\s*\(", code):
                return op
        return None

    @staticmethod
    def _extract_inaccessible_operator(payload):
        parsed_payload = payload
        if isinstance(payload, str):
            try:
                parsed_payload = json.loads(payload)
            except (TypeError, ValueError):
                parsed_payload = payload

        if isinstance(parsed_payload, dict):
            explicit_operator = parsed_payload.get("operator")
            if explicit_operator:
                return str(explicit_operator).strip()

            message = str(
                parsed_payload.get("message")
                or parsed_payload.get("detail")
                or parsed_payload.get("error")
                or parsed_payload.get("reason")
                or ""
            )
        else:
            message = str(parsed_payload or "")

        for pattern in (
            r'blocked for this account(?:/API)?\s*:\s*([A-Za-z0-9_]+)',
            r'inaccessible or unknown operator\s+"([^"]+)"',
            r'operator\s+"([^"]+)"',
        ):
            match = re.search(pattern, message, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    @staticmethod
    def _compact_payload(payload, limit=1000):
        try:
            text = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        except (TypeError, ValueError):
            text = str(payload)
        
        if len(text) <= limit:
            return text
        return text[:limit] + "...<truncated>"

    def _extract_alpha_ids(self, payload):
        """Extract alpha IDs from WorldQuant simulation progress payloads."""
        alpha_ids = []
        
        def walk(value):
            if isinstance(value, dict):
                for key in ("alpha", "alpha_id", "alphaId"):
                    alpha_value = value.get(key)
                    if isinstance(alpha_value, str):
                        alpha_ids.append(alpha_value)
                    elif isinstance(alpha_value, dict) and isinstance(alpha_value.get("id"), str):
                        alpha_ids.append(alpha_value["id"])
                
                alphas_value = value.get("alphas")
                if isinstance(alphas_value, list):
                    for item in alphas_value:
                        if isinstance(item, str):
                            alpha_ids.append(item)
                        elif isinstance(item, dict) and isinstance(item.get("id"), str):
                            alpha_ids.append(item["id"])
                
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        
        walk(payload)
        return list(dict.fromkeys(alpha_ids))

    def generate_sim_data(self, alpha_list, region, uni, neut):
        sim_data_list = []
        for candidate in alpha_list:
            if isinstance(candidate, dict):
                alpha = candidate.get("code", "")
                decay = int(candidate.get("decay", 0))
                delay = int(candidate.get("delay", 1))
                neutralization = self._normalize_neutralization(candidate.get("neutralization", neut))
                truncation = float(candidate.get("truncation", self.default_truncation))
            else:
                alpha, decay = candidate
                delay = 1
                neutralization = self._normalize_neutralization(neut)
                truncation = self.default_truncation

            simulation_data = {
                'type': 'REGULAR',
                'settings': {
                    'instrumentType': 'EQUITY',
                    'region': region,
                    'universe': uni,
                    'delay': delay,
                    'decay': decay,
                    'neutralization': neutralization,
                    'truncation': truncation,
                    'pasteurization': 'ON',
                    'unitHandling': 'VERIFY',
                    'nanHandling': 'OFF',
                    'language': 'FASTEXPR',
                    'visualization': False,
                },
                'regular': alpha}

            sim_data_list.append(simulation_data)
        return sim_data_list

    def locate_alpha(self, alpha_id):
        alpha = self.session.get("https://api.worldquantbrain.com/alphas/" + alpha_id)
        string = alpha.content.decode('utf-8')
        metrics = json.loads(string)
        #print(metrics["regular"]["code"])
        
        dateCreated = metrics["dateCreated"]
        sharpe = metrics["is"]["sharpe"]
        fitness = metrics["is"]["fitness"]
        turnover = metrics["is"]["turnover"]
        margin = metrics["is"]["margin"]
        
        triple = [sharpe, fitness, turnover, margin, dateCreated]
    
        return triple

    def get_alpha_record(self, alpha_id):
        """Fetch alpha details and return a serializable record."""
        response = self.session.get("https://api.worldquantbrain.com/alphas/" + alpha_id)
        if response.status_code == 401:
            self.login()
            response = self.session.get("https://api.worldquantbrain.com/alphas/" + alpha_id)
        response.raise_for_status()
        
        metrics = response.json()
        is_metrics = metrics.get("is", {}) or {}
        regular = metrics.get("regular", {}) or {}
        settings = metrics.get("settings", {}) or {}
        
        return {
            "alpha_id": alpha_id,
            "code": regular.get("code", ""),
            "dateCreated": metrics.get("dateCreated", ""),
            "sharpe": is_metrics.get("sharpe"),
            "fitness": is_metrics.get("fitness"),
            "turnover": is_metrics.get("turnover"),
            "margin": is_metrics.get("margin"),
            "returns": is_metrics.get("returns"),
            "drawdown": is_metrics.get("drawdown"),
            "longCount": is_metrics.get("longCount"),
            "shortCount": is_metrics.get("shortCount"),
            "region": settings.get("region"),
            "universe": settings.get("universe"),
            "delay": settings.get("delay"),
            "decay": settings.get("decay"),
            "neutralization": settings.get("neutralization"),
            "truncation": settings.get("truncation"),
        }

    def recommend_simulation_settings(self, alpha_code):
        code = str(alpha_code or "")
        operators = self._extract_expression_operators(code)
        fields = self._extract_expression_fields(code)
        settings = {
            "delay": 1,
            "decay": 0 if not self.pass_hunting_mode else 4,
            "neutralization": self.default_neutralization,
            "truncation": self.default_truncation,
        }

        if not self.pass_hunting_mode:
            return settings

        if any(token in code for token in ("ts_delta(", "ts_arg_min(", "ts_arg_max(")):
            settings["decay"] = 8
        elif any(token in code for token in ("ts_rank(", "ts_zscore(", "ts_std_dev(")):
            settings["decay"] = 6
        elif any(token in code for token in ("ts_mean(", "group_rank(", "group_zscore(", "group_neutralize(")):
            settings["decay"] = 4

        if any(token in code for token in ("group_rank(", "group_zscore(", "group_neutralize(")):
            settings["neutralization"] = "SUBINDUSTRY"

        if any(token in code for token in ("ts_arg_min(", "ts_arg_max(", "ts_product(")):
            settings["truncation"] = min(settings["truncation"], 0.04)
        else:
            settings["truncation"] = min(settings["truncation"], 0.05)

        for operator_name in operators:
            stats = self.operator_history_stats.get(operator_name, {})
            if stats.get("high_turnover_rate", 0.0) >= 0.2:
                settings["decay"] = max(settings["decay"], 8)
                settings["truncation"] = min(settings["truncation"], 0.04)
            if stats.get("concentration_rate", 0.0) >= 0.15:
                settings["neutralization"] = "SUBINDUSTRY"
                settings["truncation"] = min(settings["truncation"], 0.04)

        for field_name in fields:
            stats = self.field_history_stats.get(field_name, {})
            if stats.get("sub_universe_rate", 0.0) >= 0.3:
                settings["neutralization"] = "SUBINDUSTRY"
            if stats.get("high_turnover_rate", 0.0) >= 0.2:
                settings["decay"] = max(settings["decay"], 8)

        return settings

    def set_alpha_properties(self,
        alpha_id,
        name: str = None,
        color: str = None,
        selection_desc: str = "None",
        combo_desc: str = "None",
        tags: str = ["ace_tag"],
    ):
        """
        Function changes alpha's description parameters
        """
    
        params = {
            "color": color,
            "name": name,
            "tags": tags,
            "category": None,
            "regular": {"description": None},
            "combo": {"description": combo_desc},
            "selection": {"description": selection_desc},
        }
        response = self.session.patch(
            "https://api.worldquantbrain.com/alphas/" + alpha_id, json=params
        )
    
    def check_submission(self, alpha_bag, gold_bag, start):
        depot = []
        for idx, g in enumerate(alpha_bag):
            if idx < start:
                continue
            if idx % 5 == 0:
                print(idx)
            if idx % 200 == 0:
                self.login()
            #print(idx)
            pc = self.get_check_submission(g)
            if pc == "sleep":
                sleep(100)
                self.login()
                alpha_bag.append(g)
            elif pc != pc:
                # pc is nan
                print("check self-corrlation error")
                sleep(100)
                alpha_bag.append(g)
            elif pc == "fail":
                continue
            elif pc == "error":
                depot.append(g)
            else:
                print(g)
                gold_bag.append((g, pc))
        print(depot)
        return gold_bag

    def get_check_submission(self, alpha_id):
        check_result = self.get_submission_check_result(alpha_id)
        if check_result["status"] == "sleep":
            return "sleep"
        if check_result["status"] == "error":
            return "error"
        if not check_result["passed"]:
            return "fail"
        return check_result.get("prod_correlation")

    def get_submission_check_result(self, alpha_id):
        """Check whether an alpha passes submission checks without submitting it."""
        while True:
            result = self.session.get("https://api.worldquantbrain.com/alphas/" + alpha_id + "/check")
            if result.status_code == 401:
                self.login()
                continue
            retry_after = result.headers.get("Retry-After") or result.headers.get("retry-after")
            if retry_after:
                time.sleep(float(retry_after))
            else:
                break
        try:
            payload = result.json()
            if payload.get("is", 0) == 0:
                print("logged out")
                return {
                    "alpha_id": alpha_id,
                    "status": "sleep",
                    "passed": False,
                    "prod_correlation": None,
                    "checks": [],
                    "failed_checks": [],
                }
            
            checks = payload.get("is", {}).get("checks", [])
            checks_df = pd.DataFrame(checks)
            failed_checks = []
            prod_corr = None
            
            if not checks_df.empty:
                if "name" in checks_df.columns and "value" in checks_df.columns:
                    pc_values = checks_df[checks_df.name == "PROD_CORRELATION"]["value"].values
                    if len(pc_values) > 0:
                        prod_corr = pc_values[0]
                if "result" in checks_df.columns:
                    failed_checks = checks_df[checks_df["result"] == "FAIL"].to_dict("records")
            
            passed = len(failed_checks) == 0
            return {
                "alpha_id": alpha_id,
                "status": "ok",
                "passed": passed,
                "prod_correlation": prod_corr,
                "checks": checks,
                "failed_checks": failed_checks,
            }
        except Exception as e:
            print("catch: %s"%(alpha_id))
            logging.error(f"Error checking alpha {alpha_id}: {e}")
            return {
                "alpha_id": alpha_id,
                "status": "error",
                "passed": False,
                "prod_correlation": None,
                "checks": [],
                "failed_checks": [],
                "error": str(e),
            }

    def save_passed_alphas(self, passed_alphas, json_path="passed_alphas.json", csv_path="passed_alphas.csv"):
        """Append passed alphas to JSON and CSV files."""
        if not passed_alphas:
            return
        
        existing = []
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing = []
        
        by_id = {item.get("alpha_id"): item for item in existing if item.get("alpha_id")}
        for alpha in passed_alphas:
            by_id[alpha["alpha_id"]] = alpha
        
        merged = list(by_id.values())
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
        
        fieldnames = [
            "alpha_id", "code", "region", "universe", "delay", "decay",
            "neutralization", "truncation", "sharpe", "fitness", "turnover", "margin",
            "returns", "drawdown", "longCount", "shortCount",
            "prod_correlation", "dateCreated", "checked_at"
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(merged)
        
        logging.info(f"Saved {len(passed_alphas)} passed alphas to {json_path} and {csv_path}")
    
    def save_tested_alphas(self, tested_alphas, json_path="tested_alphas.json", csv_path="tested_alphas.csv"):
        """Append every checked alpha to JSON and CSV files."""
        if not tested_alphas:
            return
        
        existing = []
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing = []
        
        by_key = {}
        for item in existing:
            key = self._tested_alpha_storage_key(item)
            if key:
                by_key[key] = item
        
        new_count = 0
        updated_count = 0
        for alpha in tested_alphas:
            key = self._tested_alpha_storage_key(alpha)
            if not key:
                key = ("row", len(by_key), new_count)
            
            if key in by_key:
                updated_count += 1
            else:
                new_count += 1
            by_key[key] = alpha
        
        merged = list(by_key.values())
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
        
        fieldnames = [
            "alpha_id", "passed", "check_status", "failed_check_names",
            "code", "region", "universe", "delay", "decay",
            "neutralization", "truncation", "sharpe", "fitness", "turnover", "margin",
            "returns", "drawdown", "longCount", "shortCount",
            "prod_correlation", "dateCreated", "checked_at",
            "simulation_status", "simulation_error", "progress_url",
        ]
        csv_rows = []
        for alpha in merged:
            row = dict(alpha)
            failed_names = row.get("failed_check_names", [])
            if isinstance(failed_names, list):
                row["failed_check_names"] = ";".join(str(name) for name in failed_names)
            csv_rows.append(row)
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(csv_rows)
        
        logging.info(
            "Saved tested alphas to %s and %s: %s new, %s updated, %s total",
            json_path,
            csv_path,
            new_count,
            updated_count,
            len(merged),
        )

    @staticmethod
    def _tested_alpha_storage_key(record):
        if not isinstance(record, dict):
            return None
        
        alpha_id = record.get("alpha_id")
        if alpha_id:
            return ("id", str(alpha_id))
        
        code = str(record.get("code") or "").strip()
        if not code:
            return None
        
        return (
            "signature",
            code,
            str(record.get("region") or "").upper(),
            str(record.get("universe") or "").upper(),
            str(record.get("delay")),
            str(record.get("decay")),
            str(record.get("neutralization") or "").upper(),
        )
            
    def get_vec_fields(self, fields):
        vec_fields = []
     
        for field in fields:
            for vec_op in self.safe_vector_ops:
                if vec_op == "vec_choose":
                    vec_fields.append("%s(%s, nth=-1)"%(vec_op, field))
                    vec_fields.append("%s(%s, nth=0)"%(vec_op, field))
                else:
                    vec_fields.append("%s(%s)"%(vec_op, field))
     
        return(vec_fields)

    def get_datafields(self,
        instrument_type: str = 'EQUITY',
        region: str = 'USA',
        delay: int = 1,
        universe: str = 'TOP3000',
        dataset_id: str = '',
        search: str = ''
    ):
        base_url = "https://api.worldquantbrain.com/data-fields"
        limit = 50
        params = {
            "instrumentType": instrument_type,
            "region": region,
            "delay": delay,
            "universe": universe,
            "limit": limit,
        }
        if dataset_id:
            params["dataset.id"] = dataset_id
        if search:
            params["search"] = search
        
        def fetch_page(offset):
            page_params = dict(params)
            page_params["offset"] = offset
            
            for attempt in range(3):
                response = self.session.get(base_url, params=page_params)
                if response.status_code == 401:
                    logging.info("Session expired while fetching data fields, re-authenticating...")
                    self.login()
                    continue
                
                retry_after = response.headers.get("Retry-After") or response.headers.get("retry-after")
                if retry_after:
                    sleep(float(retry_after))
                    continue
                
                if response.status_code != 200:
                    logging.warning(
                        "Data fields request failed: status=%s, body=%s",
                        response.status_code,
                        response.text[:300],
                    )
                    sleep(2 * (attempt + 1))
                    continue
                
                payload = response.json()
                if "results" not in payload:
                    logging.warning("Data fields payload missing results at offset %s: %s", offset, payload)
                    sleep(2 * (attempt + 1))
                    continue
                
                return payload
            
            return {"count": 0, "results": []}
        
        first_payload = fetch_page(0)
        count = first_payload.get("count", len(first_payload.get("results", [])))
        if search and not count:
            count = 100
        
        datafields_list = [first_payload.get("results", [])]
        for x in range(limit, count, limit):
            payload = fetch_page(x)
            results = payload.get("results", [])
            if not results:
                logging.info("No more data fields returned at offset %s", x)
                break
            datafields_list.append(results)
     
        datafields_list_flat = [item for sublist in datafields_list for item in sublist]
     
        datafields_df = pd.DataFrame(datafields_list_flat)
        return datafields_df

    def process_datafields(self, df, data_type):
        if data_type == "matrix":
            fields_df = df[df["type"] == "MATRIX"]
            prioritized_records = self._prioritize_datafield_records(fields_df, data_type, self.max_matrix_fields)
            datafields = [record["id"] for record in prioritized_records if record.get("id")]
        elif data_type == "vector":
            fields_df = df[df["type"] == "VECTOR"]
            prioritized_records = self._prioritize_datafield_records(fields_df, data_type, self.max_vector_fields)
            datafields = self.get_vec_fields([record["id"] for record in prioritized_records if record.get("id")])
        else:
            return []

        tb_fields = []
        for field in datafields:
            tb_fields.append("winsorize(ts_backfill(%s, 120), std=4)"%field)
        return tb_fields

    def _prioritize_datafield_records(self, fields_df, data_type, limit):
        if fields_df is None or fields_df.empty:
            return []

        records = fields_df.to_dict("records")

        def as_float(value, default=0.0):
            try:
                if value in (None, ""):
                    return default
                return float(value)
            except (TypeError, ValueError):
                return default

        def field_score(record):
            user_count = as_float(record.get("userCount"))
            alpha_count = as_float(record.get("alphaCount"))
            pyramid_multiplier = as_float(record.get("pyramidMultiplier"), 1.0)
            coverage = as_float(record.get("coverage"))
            usage = user_count + alpha_count
            field_id = str(record.get("id") or "")
            description = str(record.get("description") or "")
            text = f"{field_id} {description}".lower()
            history_stats = self.field_history_stats.get(field_id, {})
            history_score = self.field_history_scores.get(field_id, 0.0)

            score = pyramid_multiplier * 2.0
            score += coverage * 0.5
            score -= min(6.0, math.log1p(max(usage, 0.0)))
            score += history_score * 1.1

            if user_count <= 5 and alpha_count <= 10:
                score += 2.0
            elif user_count <= 20 and alpha_count <= 50:
                score += 1.0

            if data_type == "matrix":
                score += 0.25

            if any(token in text for token in ("currency", "country", "exchange", "ticker", "cusip", "isin", "sedol")):
                score -= 1.5

            if history_stats.get("count", 0) >= 4:
                score -= history_stats.get("sub_universe_rate", 0.0) * 1.0
                score -= history_stats.get("concentration_rate", 0.0) * 0.8
                score -= history_stats.get("high_turnover_rate", 0.0) * 0.5

            return score

        prioritized = sorted(records, key=field_score, reverse=True)
        logging.info(
            "Prioritized %s %s fields for pass hunting; top picks: %s",
            min(limit, len(prioritized)),
            data_type,
            [record.get("id") for record in prioritized[:min(5, len(prioritized))]],
        )
        return prioritized[:limit]
     
    def view_alphas(self, gold_bag):
        sharp_list = []
        for gold, pc in gold_bag:

            triple = self.locate_alpha(gold)
            info = [triple[2], triple[3], triple[4], triple[5], triple[6], triple[1]]
            info.append(pc)
            sharp_list.append(info)

        sharp_list.sort(reverse=True, key = lambda x : x[3])
        for i in sharp_list:
            print(i)
     
    def get_alphas(self, start_date, end_date, sharpe_th, fitness_th, region, alpha_num, usage):
        next_alphas = []
        decay_alphas = []
        # 3E large 3C less
        count = 0
        for i in range(0, alpha_num, 100):
            print(i)
            url_e = "https://api.worldquantbrain.com/users/self/alphas?limit=100&offset=%d"%(i) \
                    + "&status=UNSUBMITTED%1FIS_FAIL&dateCreated%3E=2025-" + start_date  \
                    + "T00:00:00-04:00&dateCreated%3C2025-" + end_date \
                    + "T00:00:00-04:00&is.fitness%3E" + str(fitness_th) + "&is.sharpe%3E" \
                    + str(sharpe_th) + "&settings.region=" + region + "&order=-is.sharpe&hidden=false&type!=SUPER"
            url_c = "https://api.worldquantbrain.com/users/self/alphas?limit=100&offset=%d"%(i) \
                    + "&status=UNSUBMITTED%1FIS_FAIL&dateCreated%3E=2025-" + start_date  \
                    + "T00:00:00-04:00&dateCreated%3C2025-" + end_date \
                    + "T00:00:00-04:00&is.fitness%3C-" + str(fitness_th) + "&is.sharpe%3C-" \
                    + str(sharpe_th) + "&settings.region=" + region + "&order=is.sharpe&hidden=false&type!=SUPER"
            urls = [url_e]
            if usage != "submit":
                urls.append(url_c)
            for url in urls:
                response = self.session.get(url)
                #print(response.json())
                try:
                    alpha_list = response.json()["results"]
                    #print(response.json())
                    for j in range(len(alpha_list)):
                        alpha_id = alpha_list[j]["id"]
                        name = alpha_list[j]["name"]
                        dateCreated = alpha_list[j]["dateCreated"]
                        sharpe = alpha_list[j]["is"]["sharpe"]
                        fitness = alpha_list[j]["is"]["fitness"]
                        turnover = alpha_list[j]["is"]["turnover"]
                        margin = alpha_list[j]["is"]["margin"]
                        longCount = alpha_list[j]["is"]["longCount"]
                        shortCount = alpha_list[j]["is"]["shortCount"]
                        decay = alpha_list[j]["settings"]["decay"]
                        exp = alpha_list[j]['regular']['code']
                        count += 1
                        #if (sharpe > 1.2 and sharpe < 1.6) or (sharpe < -1.2 and sharpe > -1.6):
                        if (longCount + shortCount) > 100:
                            if sharpe < -1.2:
                                exp = "-%s"%exp
                            rec = [alpha_id, exp, sharpe, turnover, fitness, margin, dateCreated, decay]
                            print(rec)
                            if turnover > 0.7:
                                rec.append(decay*4)
                                decay_alphas.append(rec)
                            elif turnover > 0.6:
                                rec.append(decay*3+3)
                                decay_alphas.append(rec)
                            elif turnover > 0.5:
                                rec.append(decay*3)
                                decay_alphas.append(rec)
                            elif turnover > 0.4:
                                rec.append(decay*2)
                                decay_alphas.append(rec)
                            elif turnover > 0.35:
                                rec.append(decay+4)
                                decay_alphas.append(rec)
                            elif turnover > 0.3:
                                rec.append(decay+2)
                                decay_alphas.append(rec)
                            else:
                                next_alphas.append(rec)
                except:
                    print("%d finished re-login"%i)
                    self.login()

        output_dict = {"next" : next_alphas, "decay" : decay_alphas}
        print("count: %d"%count)
        return output_dict
     
    def transform(self, next_alpha_recs, region):
        output = []
        for rec in next_alpha_recs:
            
            decay = rec[-1]
            exp = rec[1]
            output.append([exp,decay])
        output_dict = {region : output}
        return output_dict

    def prune(self, next_alpha_recs, region, prefix, keep_num):
        # prefix is the datafield prefix, fnd6, mdl175 ...
        # keep_num is the num of top sharpe same-datafield alpha
        output = []
        num_dict = defaultdict(int)
        for rec in next_alpha_recs:
            exp = rec[1]
            field = exp.split(prefix)[-1].split(",")[0]
            sharpe = rec[2]
            if sharpe < 0:
                field = "-%s"%field
            if num_dict[field] < keep_num:
                num_dict[field] += 1
                decay = rec[-1]
                exp = rec[1]
                output.append([exp,decay])
        output_dict = {region : output}
        return output_dict

    def get_first_order(self, vec_fields, ops_set):
        per_field_candidates = []
        for field in vec_fields:
            candidates = self._build_field_candidates(field, vec_fields, ops_set)
            if candidates:
                per_field_candidates.append(candidates)

        alpha_set = []
        seen = set()
        max_len = max((len(candidates) for candidates in per_field_candidates), default=0)
        for index in range(max_len):
            for candidates in per_field_candidates:
                if index >= len(candidates):
                    continue
                alpha = candidates[index]
                if alpha in seen:
                    continue
                seen.add(alpha)
                alpha_set.append(alpha)
        return alpha_set

    def _build_field_candidates(self, field, all_fields, ops_set):
        candidates = []
        seen = set()

        def add(alpha):
            if self._first_blocked_operator(alpha):
                return
            if alpha and alpha not in seen:
                seen.add(alpha)
                candidates.append(alpha)

        if self.pass_hunting_mode:
            curated_candidates = [
                f"group_neutralize(ts_rank({field}, 22), industry)",
                f"group_neutralize(ts_rank({field}, 66), subindustry)",
                f"group_zscore(ts_zscore({field}, 66), sector)",
                f"group_rank(ts_mean({field}, 22), sector)",
                f"group_rank(ts_mean({field}, 66), industry)",
                f"group_neutralize(ts_delta({field}, 22), industry)",
                f"group_rank(ts_std_dev({field}, 22), sector)",
                f"group_rank(ts_arg_min({field}, 120), sector)",
                f"group_rank(ts_arg_max({field}, 120), sector)",
                f"scale(group_neutralize(ts_std_dev({field}, 66), subindustry))",
                f"scale(group_neutralize(ts_mean({field}, 120), industry))",
            ]
            for alpha in curated_candidates:
                add(alpha)

        add(field)

        for op in self._ordered_candidate_ops(ops_set):
            if op == "ts_percentage":
                for alpha in self.ts_comp_factory(op, field, "percentage", [0.5]):
                    add(alpha)
            elif op == "ts_decay_exp_window":
                for alpha in self.ts_comp_factory(op, field, "factor", [0.5]):
                    add(alpha)
            elif op == "ts_moment":
                for alpha in self.ts_comp_factory(op, field, "k", [2, 3, 4]):
                    add(alpha)
            elif op == "ts_entropy":
                for alpha in self.ts_comp_factory(op, field, "buckets", [10]):
                    add(alpha)
            elif op in twin_field_ops:
                for alpha in self.twin_field_factory(op, field, all_fields):
                    add(alpha)
            elif op.startswith("ts_") or op == "inst_tvr":
                for alpha in self.ts_factory(op, field):
                    add(alpha)
            elif op.startswith("group_"):
                for alpha in self.group_factory(op, field, "usa"):
                    add(alpha)
            elif op.startswith("vector"):
                for alpha in self.vector_factory(op, field):
                    add(alpha)
            elif op == "signed_power":
                add("%s(%s, 2)" % (op, field))
            else:
                add("%s(%s)" % (op, field))

            if self.pass_hunting_mode and len(candidates) >= self.max_candidates_per_field:
                break

        if self.pass_hunting_mode:
            candidates = sorted(
                candidates,
                key=lambda alpha: (self._history_expression_score(alpha), -len(alpha)),
                reverse=True,
            )

        return candidates[:self.max_candidates_per_field]

    def _ordered_candidate_ops(self, ops_set):
        if not self.pass_hunting_mode:
            return ops_set

        preferred_ops = [
            "ts_std_dev",
            "ts_mean",
            "ts_rank",
            "ts_zscore",
            "ts_delta",
            "ts_sum",
            "ts_arg_min",
            "ts_arg_max",
            "rank",
            "zscore",
            "normalize",
        ]
        available_ops = [op for op in preferred_ops if op in ops_set]
        return sorted(
            available_ops,
            key=lambda op: (
                self.operator_history_scores.get(op, 0.0),
                -self.operator_history_stats.get(op, {}).get("high_turnover_rate", 0.0),
                -self.operator_history_stats.get(op, {}).get("concentration_rate", 0.0),
            ),
            reverse=True,
        )
        
    def get_group_second_order_factory(self, first_order, group_ops, region):
        second_order = []
        for fo in first_order:
            for group_op in group_ops:
                second_order += self.group_factory(group_op, fo, region)
        return second_order
     
    def get_ts_second_order_factory(self, first_order, ts_ops):
        second_order = []
        for fo in first_order:
            for ts_op in ts_ops:
                second_order += self.ts_factory(ts_op, fo)
        return second_order
     
     
    def get_data_fields_csv(self, filename, prefix):
        '''
        inputs: 
        CSV file with header 'field' 
        outputs:
        A list of string
        '''
        df = pd.read_csv(filename,header=0,encoding = 'unicode_escape')
        collection = []
        for _, row in df.iterrows():
            if row['field'].startswith(prefix):
                collection.append(row['field'])
     
        return collection
     
    def ts_arith_factory(self, ts_op, arith_op, field):
        first_order = "%s(%s)"%(arith_op, field)
        second_order = self.ts_factory(ts_op, first_order)
        return second_order
     
    def arith_ts_factory(self, arith_op, ts_op, field):
        second_order = []
        first_order = self.ts_factory(ts_op, field)
        for fo in first_order:
            second_order.append("%s(%s)"%(arith_op, fo))
        return second_order
     
    def ts_group_factory(self, ts_op, group_op, field, region):
        second_order = []
        first_order = self.group_factory(group_op, field, region)
        for fo in first_order:
            second_order += self.ts_factory(ts_op, fo)
        return second_order
     
    def group_ts_factory(self, group_op, ts_op, field, region):
        second_order = []
        first_order = self.ts_factory(ts_op, field)
        for fo in first_order:
            second_order += self.group_factory(group_op, fo, region)
        return second_order
     
    def vector_factory(self, op, field):
        output = []
        vectors = ["cap"]
        
        for vector in vectors:
        
            alpha = "%s(%s, %s)"%(op, field, vector)
            output.append(alpha)
        
        return output
     
    def trade_when_factory(self, op,field,region):
        output = []
        open_events = ["ts_arg_max(volume, 5) == 0", "ts_corr(close, volume, 20) < 0",
                       "ts_corr(close, volume, 5) < 0", "ts_mean(volume,10)>ts_mean(volume,60)",
                       "group_rank(ts_std_dev(returns,60), sector) > 0.7", "ts_zscore(returns,60) > 2",
                       "ts_skewness(returns,120)> 0.7", "ts_arg_min(volume, 5) > 3",
                       "ts_std_dev(returns, 5) > ts_std_dev(returns, 20)",
                       "ts_arg_max(close, 5) == 0", "ts_arg_max(close, 20) == 0",
                       "ts_corr(close, volume, 5) > 0", "ts_corr(close, volume, 5) > 0.3", "ts_corr(close, volume, 5) > 0.5",
                       "ts_corr(close, volume, 20) > 0", "ts_corr(close, volume, 20) > 0.3", "ts_corr(close, volume, 20) > 0.5",
                       "ts_regression(returns, %s, 5, lag = 0, rettype = 2) > 0"%field,
                       "ts_regression(returns, %s, 20, lag = 0, rettype = 2) > 0"%field,
                       "ts_regression(returns, ts_step(20), 20, lag = 0, rettype = 2) > 0",
                       "ts_regression(returns, ts_step(5), 5, lag = 0, rettype = 2) > 0"]

        exit_events = ["abs(returns) > 0.1", "-1", "days_from_last_change(ern3_pre_reptime) > 20"]

        usa_events = ["rank(rp_css_business) > 0.8", "ts_rank(rp_css_business, 22) > 0.8", "rank(vec_avg(mws82_sentiment)) > 0.8",
                      "ts_rank(vec_avg(mws82_sentiment),22) > 0.8", "rank(vec_avg(nws48_ssc)) > 0.8",
                      "ts_rank(vec_avg(nws48_ssc),22) > 0.8", "rank(vec_avg(mws50_ssc)) > 0.8", "ts_rank(vec_avg(mws50_ssc),22) > 0.8",
                      "ts_rank(vec_sum(scl12_alltype_buzzvec),22) > 0.9", "pcr_oi_270 < 1", "pcr_oi_270 > 1",]

        asi_events = ["rank(vec_avg(mws38_score)) > 0.8", "ts_rank(vec_avg(mws38_score),22) > 0.8"]

        eur_events = ["rank(rp_css_business) > 0.8", "ts_rank(rp_css_business, 22) > 0.8",
                      "rank(vec_avg(oth429_research_reports_fundamental_keywords_4_method_2_pos)) > 0.8",
                      "ts_rank(vec_avg(oth429_research_reports_fundamental_keywords_4_method_2_pos),22) > 0.8",
                      "rank(vec_avg(mws84_sentiment)) > 0.8", "ts_rank(vec_avg(mws84_sentiment),22) > 0.8",
                      "rank(vec_avg(mws85_sentiment)) > 0.8", "ts_rank(vec_avg(mws85_sentiment),22) > 0.8",
                      "rank(mdl110_analyst_sentiment) > 0.8", "ts_rank(mdl110_analyst_sentiment, 22) > 0.8",
                      "rank(vec_avg(nws3_scores_posnormscr)) > 0.8",
                      "ts_rank(vec_avg(nws3_scores_posnormscr),22) > 0.8",
                      "rank(vec_avg(mws36_sentiment_words_positive)) > 0.8",
                      "ts_rank(vec_avg(mws36_sentiment_words_positive),22) > 0.8"]

        glb_events = ["rank(vec_avg(mdl109_news_sent_1m)) > 0.8",
                      "ts_rank(vec_avg(mdl109_news_sent_1m),22) > 0.8",
                      "rank(vec_avg(nws20_ssc)) > 0.8",
                      "ts_rank(vec_avg(nws20_ssc),22) > 0.8",
                      "vec_avg(nws20_ssc) > 0",
                      "rank(vec_avg(nws20_bee)) > 0.8",
                      "ts_rank(vec_avg(nws20_bee),22) > 0.8",
                      "rank(vec_avg(nws20_qmb)) > 0.8",
                      "ts_rank(vec_avg(nws20_qmb),22) > 0.8"]

        chn_events = ["rank(vec_avg(oth111_xueqiunaturaldaybasicdivisionstat_senti_conform)) > 0.8",
                      "ts_rank(vec_avg(oth111_xueqiunaturaldaybasicdivisionstat_senti_conform),22) > 0.8",
                      "rank(vec_avg(oth111_gubanaturaldaydevicedivisionstat_senti_conform)) > 0.8",
                      "ts_rank(vec_avg(oth111_gubanaturaldaydevicedivisionstat_senti_conform),22) > 0.8",
                      "rank(vec_avg(oth111_baragedivisionstat_regi_senti_conform)) > 0.8",
                      "ts_rank(vec_avg(oth111_baragedivisionstat_regi_senti_conform),22) > 0.8"]

        kor_events = ["rank(vec_avg(mdl110_analyst_sentiment)) > 0.8",
                      "ts_rank(vec_avg(mdl110_analyst_sentiment),22) > 0.8",
                      "rank(vec_avg(mws38_score)) > 0.8",
                      "ts_rank(vec_avg(mws38_score),22) > 0.8"]

        twn_events = ["rank(vec_avg(mdl109_news_sent_1m)) > 0.8",
                      "ts_rank(vec_avg(mdl109_news_sent_1m),22) > 0.8",
                      "rank(rp_ess_business) > 0.8",
                      "ts_rank(rp_ess_business,22) > 0.8"]

        for oe in open_events:
            for ee in exit_events:
                alpha = "%s(%s, %s, %s)"%(op, oe, field, ee)
                output.append(alpha)
        return output
     
    def ts_factory(self, op, field):
        output = []
        if self.pass_hunting_mode:
            days = [22, 66, 120, 240]
        else:
            days = [5, 22, 66, 120, 240]
        
        for day in days:
        
            alpha = "%s(%s, %d)"%(op, field, day)
            output.append(alpha)
        
        return output
     
    def ts_comp_factory(self, op, field, factor, paras):
        output = []
        #l1, l2 = [3, 5, 10, 20, 60, 120, 240], paras
        l1, l2 = [5, 22, 66, 240], paras
        comb = list(product(l1, l2))
        
        for day,para in comb:
            
            if type(para) == float:
                alpha = "%s(%s, %d, %s=%.1f)"%(op, field, day, factor, para)
            elif type(para) == int:
                alpha = "%s(%s, %d, %s=%d)"%(op, field, day, factor, para)
            
            output.append(alpha)
        
        return output
     
    def twin_field_factory(self, op, field, fields):
        
        output = []
        #days = [3, 5, 10, 20, 60, 120, 240]
        days = [5, 22, 66, 240]
        outset = list(set(fields) - set([field]))
        
        for day in days:
            for counterpart in outset:
                alpha = "%s(%s, %s, %d)"%(op, field, counterpart, day)
                output.append(alpha)
        
        return output
     
     
    def group_factory(self, op, field, region):
        output = []
        vectors = ["cap"] 
        
        chn_group_13 = ['pv13_h_min2_sector', 'pv13_di_6l', 'pv13_rcsed_6l', 'pv13_di_5l', 'pv13_di_4l', 
                            'pv13_di_3l', 'pv13_di_2l', 'pv13_di_1l', 'pv13_parent', 'pv13_level']
        
        
        chn_group_1 = ['sta1_top3000c30','sta1_top3000c20','sta1_top3000c10','sta1_top3000c2','sta1_top3000c5']
        
        chn_group_2 = ['sta2_top3000_fact4_c10','sta2_top2000_fact4_c50','sta2_top3000_fact3_c20']
     
        chn_group_7 = ['oth171_region_sector_long_d1_sector', 'oth171_region_sector_short_d1_sector', 
                       'oth171_sector_long_d1_sector', 'oth171_sector_short_d1_sector']
        
        hkg_group_13 = ['pv13_10_f3_g2_minvol_1m_sector', 'pv13_10_minvol_1m_sector', 'pv13_20_minvol_1m_sector', 
                        'pv13_2_minvol_1m_sector', 'pv13_5_minvol_1m_sector', 'pv13_1l_scibr', 'pv13_3l_scibr',
                        'pv13_2l_scibr', 'pv13_4l_scibr', 'pv13_5l_scibr']
        
        hkg_group_1 = ['sta1_allc50','sta1_allc5','sta1_allxjp_513_c20','sta1_top2000xjp_513_c5']
        
        hkg_group_2 = ['sta2_all_xjp_513_all_fact4_c10','sta2_top2000_xjp_513_top2000_fact3_c10',
                       'sta2_allfactor_xjp_513_13','sta2_top2000_xjp_513_top2000_fact3_c20']
        
        hkg_group_8 = ['oth455_relation_n2v_p10_q50_w5_kmeans_cluster_5',
                         'oth455_relation_n2v_p10_q50_w4_kmeans_cluster_10',
                         'oth455_relation_n2v_p10_q50_w1_kmeans_cluster_20',
                         'oth455_partner_n2v_p50_q200_w4_kmeans_cluster_5', 
                         'oth455_partner_n2v_p10_q50_w4_pca_fact3_cluster_10',
                         'oth455_customer_n2v_p50_q50_w1_kmeans_cluster_5']
        
        twn_group_13 = ['pv13_2_minvol_1m_sector','pv13_20_minvol_1m_sector','pv13_10_minvol_1m_sector',
                        'pv13_5_minvol_1m_sector','pv13_10_f3_g2_minvol_1m_sector','pv13_5_f3_g2_minvol_1m_sector',
                        'pv13_2_f4_g3_minvol_1m_sector']
        
        twn_group_1 = ['sta1_allc50','sta1_allxjp_513_c50','sta1_allxjp_513_c20','sta1_allxjp_513_c2',
                       'sta1_allc20','sta1_allxjp_513_c5','sta1_allxjp_513_c10','sta1_allc2','sta1_allc5']
        
        twn_group_2 = ['sta2_allfactor_xjp_513_0','sta2_all_xjp_513_all_fact3_c20',
                       'sta2_all_xjp_513_all_fact4_c20','sta2_all_xjp_513_all_fact4_c50']
        
        twn_group_8 = ['oth455_relation_n2v_p50_q200_w1_pca_fact1_cluster_20',
                         'oth455_relation_n2v_p10_q50_w3_kmeans_cluster_20',
                         'oth455_relation_roam_w3_pca_fact2_cluster_5',
                         'oth455_relation_n2v_p50_q50_w2_pca_fact2_cluster_10', 
                         'oth455_relation_n2v_p10_q200_w5_pca_fact2_cluster_20',
                         'oth455_relation_n2v_p50_q50_w5_kmeans_cluster_5']
        
        usa_group_13 = ['pv13_h_min2_3000_sector','pv13_r2_min20_3000_sector','pv13_r2_min2_3000_sector',
                        'pv13_r2_min2_3000_sector', 'pv13_h_min2_focused_pureplay_3000_sector']
        
        usa_group_1 = ['sta1_top3000c50','sta1_allc20','sta1_allc10','sta1_top3000c20','sta1_allc5']
        
        usa_group_2 = ['sta2_top3000_fact3_c50','sta2_top3000_fact4_c20','sta2_top3000_fact4_c10']
        
        usa_group_3 = ['sta3_2_sector', 'sta3_3_sector', 'sta3_news_sector', 'sta3_peer_sector',
                       'sta3_pvgroup1_sector', 'sta3_pvgroup2_sector', 'sta3_pvgroup3_sector', 'sta3_sec_sector']
        
        usa_group_4 = ['rsk69_01c_1m', 'rsk69_57c_1m', 'rsk69_02c_2m', 'rsk69_5c_2m', 'rsk69_02c_1m',
                       'rsk69_05c_2m', 'rsk69_57c_2m', 'rsk69_5c_1m', 'rsk69_05c_1m', 'rsk69_01c_2m']
        
        usa_group_5 = ['anl52_2000_backfill_d1_05c', 'anl52_3000_d1_05c', 'anl52_3000_backfill_d1_02c', 
                       'anl52_3000_backfill_d1_5c', 'anl52_3000_backfill_d1_05c', 'anl52_3000_d1_5c']
        
        usa_group_6 = ['mdl10_group_name']
        
        usa_group_7 = ['oth171_region_sector_long_d1_sector', 'oth171_region_sector_short_d1_sector', 
                       'oth171_sector_long_d1_sector', 'oth171_sector_short_d1_sector']
        
        usa_group_8 = ['oth455_competitor_n2v_p10_q50_w1_kmeans_cluster_10',
                         'oth455_customer_n2v_p10_q50_w5_kmeans_cluster_10',
                         'oth455_relation_n2v_p50_q200_w5_kmeans_cluster_20',
                         'oth455_competitor_n2v_p50_q50_w3_kmeans_cluster_10', 
                         'oth455_relation_n2v_p50_q50_w3_pca_fact2_cluster_10', 
                         'oth455_partner_n2v_p10_q50_w2_pca_fact2_cluster_5',
                         'oth455_customer_n2v_p50_q50_w3_kmeans_cluster_5',
                         'oth455_competitor_n2v_p50_q200_w5_kmeans_cluster_20']
        
        
        asi_group_13 = ['pv13_20_minvol_1m_sector', 'pv13_5_f3_g2_minvol_1m_sector', 'pv13_10_f3_g2_minvol_1m_sector',
                        'pv13_2_f4_g3_minvol_1m_sector', 'pv13_10_minvol_1m_sector', 'pv13_5_minvol_1m_sector']
        
        asi_group_1 = ['sta1_allc50', 'sta1_allc10', 'sta1_minvol1mc50','sta1_minvol1mc20',
                       'sta1_minvol1m_normc20', 'sta1_minvol1m_normc50']
        
        asi_group_8 = ['oth455_partner_roam_w3_pca_fact1_cluster_5',
                       'oth455_relation_roam_w3_pca_fact1_cluster_20',
                       'oth455_relation_roam_w3_kmeans_cluster_20',
                       'oth455_relation_n2v_p10_q200_w5_pca_fact1_cluster_20',
                       'oth455_relation_n2v_p10_q200_w5_pca_fact1_cluster_20',
                       'oth455_competitor_n2v_p10_q200_w1_kmeans_cluster_10']
        
        jpn_group_1 = ['sta1_alljpn_513_c5', 'sta1_alljpn_513_c50', 'sta1_alljpn_513_c2', 'sta1_alljpn_513_c20']
        
        jpn_group_2 = ['sta2_top2000_jpn_513_top2000_fact3_c20', 'sta2_all_jpn_513_all_fact1_c5',
                       'sta2_allfactor_jpn_513_9', 'sta2_all_jpn_513_all_fact1_c10']
        
        jpn_group_8 = ['oth455_customer_n2v_p50_q50_w5_kmeans_cluster_10', 
                       'oth455_customer_n2v_p50_q50_w4_kmeans_cluster_10', 
                       'oth455_customer_n2v_p50_q50_w3_kmeans_cluster_10', 
                       'oth455_customer_n2v_p50_q50_w2_kmeans_cluster_10',
                       'oth455_customer_n2v_p50_q200_w5_kmeans_cluster_10',
                       'oth455_customer_n2v_p50_q200_w5_kmeans_cluster_10']
        
        jpn_group_13 = ['pv13_2_minvol_1m_sector', 'pv13_2_f4_g3_minvol_1m_sector', 'pv13_10_minvol_1m_sector',
                        'pv13_10_f3_g2_minvol_1m_sector', 'pv13_all_delay_1_parent', 'pv13_all_delay_1_level']
        
        kor_group_13 = ['pv13_10_f3_g2_minvol_1m_sector', 'pv13_5_minvol_1m_sector', 'pv13_5_f3_g2_minvol_1m_sector',
                        'pv13_2_minvol_1m_sector', 'pv13_20_minvol_1m_sector', 'pv13_2_f4_g3_minvol_1m_sector']
        
        kor_group_1 = ['sta1_allc20','sta1_allc50','sta1_allc2','sta1_allc10','sta1_minvol1mc50',
                       'sta1_allxjp_513_c10', 'sta1_top2000xjp_513_c50']
        
        kor_group_2 =['sta2_all_xjp_513_all_fact1_c50','sta2_top2000_xjp_513_top2000_fact2_c50',
                      'sta2_all_xjp_513_all_fact4_c50','sta2_all_xjp_513_all_fact4_c5']
        
        kor_group_8 = ['oth455_relation_n2v_p50_q200_w3_pca_fact3_cluster_5',
                         'oth455_relation_n2v_p50_q50_w4_pca_fact2_cluster_10',
                         'oth455_relation_n2v_p50_q200_w5_pca_fact2_cluster_5',
                         'oth455_relation_n2v_p50_q200_w4_kmeans_cluster_10', 
                         'oth455_relation_n2v_p10_q50_w1_kmeans_cluster_10', 
                         'oth455_relation_n2v_p50_q50_w5_pca_fact1_cluster_20']
        
        eur_group_13 = ['pv13_5_sector', 'pv13_2_sector', 'pv13_v3_3l_scibr', 'pv13_v3_2l_scibr', 'pv13_2l_scibr',
                        'pv13_52_sector', 'pv13_v3_6l_scibr', 'pv13_v3_4l_scibr', 'pv13_v3_1l_scibr']
        
        eur_group_1 = ['sta1_allc10', 'sta1_allc2', 'sta1_top1200c2', 'sta1_allc20', 'sta1_top1200c10']
        
        eur_group_2 = ['sta2_top1200_fact3_c50','sta2_top1200_fact3_c20','sta2_top1200_fact4_c50']
        
        eur_group_3 = ['sta3_6_sector', 'sta3_pvgroup4_sector', 'sta3_pvgroup5_sector']
        
        eur_group_7 = ['oth171_region_sector_long_d1_sector', 'oth171_region_sector_short_d1_sector', 
                       'oth171_sector_long_d1_sector', 'oth171_sector_short_d1_sector']
        
        eur_group_8 = ['oth455_relation_n2v_p50_q200_w3_pca_fact1_cluster_5',
                         'oth455_competitor_n2v_p50_q200_w4_kmeans_cluster_20',
                         'oth455_competitor_n2v_p50_q200_w5_pca_fact1_cluster_10', 
                         'oth455_competitor_roam_w4_pca_fact2_cluster_20', 
                         'oth455_relation_n2v_p10_q200_w2_pca_fact2_cluster_20', 
                         'oth455_competitor_roam_w2_pca_fact3_cluster_20']
        
        glb_group_13 = ["pv13_10_f2_g3_sector", "pv13_2_f3_g2_sector", "pv13_2_sector", "pv13_52_all_delay_1_sector"]
        
        glb_group_3 = ['sta3_2_sector', 'sta3_3_sector', 'sta3_news_sector', 'sta3_peer_sector',
                       'sta3_pvgroup1_sector', 'sta3_pvgroup2_sector', 'sta3_pvgroup3_sector', 'sta3_sec_sector']
        
        glb_group_1 = ['sta1_allc20', 'sta1_allc10', 'sta1_allc50', 'sta1_allc5']
        
        glb_group_2 = ['sta2_all_fact4_c50', 'sta2_all_fact4_c20', 'sta2_all_fact3_c20', 'sta2_all_fact4_c10']
        
        glb_group_13 = ['pv13_2_sector', 'pv13_10_sector', 'pv13_3l_scibr', 'pv13_2l_scibr', 'pv13_1l_scibr',
                        'pv13_52_minvol_1m_all_delay_1_sector','pv13_52_minvol_1m_sector','pv13_52_minvol_1m_sector']
        
        glb_group_7 = ['oth171_region_sector_long_d1_sector', 'oth171_region_sector_short_d1_sector', 
                       'oth171_sector_long_d1_sector', 'oth171_sector_short_d1_sector']  
        
        glb_group_8 = ['oth455_relation_n2v_p10_q200_w5_kmeans_cluster_5',
                         'oth455_relation_n2v_p10_q50_w2_kmeans_cluster_5',
                         'oth455_relation_n2v_p50_q200_w5_kmeans_cluster_5', 
                         'oth455_customer_n2v_p10_q50_w4_pca_fact3_cluster_20', 
                         'oth455_competitor_roam_w2_pca_fact1_cluster_10', 
                         'oth455_relation_n2v_p10_q200_w2_kmeans_cluster_5']
        
        amr_group_13 = ['pv13_4l_scibr', 'pv13_1l_scibr', 'pv13_hierarchy_min51_f1_sector',
                        'pv13_hierarchy_min2_600_sector', 'pv13_r2_min2_sector', 'pv13_h_min20_600_sector']
        
        amr_group_3 = ['sta3_news_sector', 'sta3_peer_sector', 'sta3_pvgroup1_sector', 'sta3_pvgroup2_sector',
                       'sta3_pvgroup3_sector']
        
        amr_group_8 = ['oth455_relation_roam_w1_pca_fact2_cluster_10', 
                       'oth455_competitor_n2v_p50_q50_w4_kmeans_cluster_10', 
                       'oth455_competitor_n2v_p50_q50_w3_kmeans_cluster_10', 
                       'oth455_competitor_n2v_p50_q50_w2_kmeans_cluster_10', 
                       'oth455_competitor_n2v_p50_q50_w1_kmeans_cluster_10',
                       'oth455_competitor_n2v_p50_q200_w5_kmeans_cluster_10']
        
        group_3 = ["oth171_region_sector_long_d1_sector", "oth171_region_sector_short_d1_sector",
                   "oth171_sector_long_d1_sector", "oth171_sector_short_d1_sector"]
        
        bps_group = "bucket(rank(fnd28_value_05480/close), range='0.2, 1, 0.2')"
        cap_group = "bucket(rank(cap), range='0.1, 1, 0.1')"
        sector_cap_group = "bucket(group_rank(cap,sector),range='0,1,0.1')"
        vol_group = "bucket(rank(ts_std_dev(ts_returns(close,1),20)),range = '0.1,1,0.1')"
        
        groups = ["market","sector", "industry", "subindustry", bps_group, cap_group, sector_cap_group]
        
        if region == "chn":
            groups += chn_group_13 + chn_group_1 + chn_group_2 + group_3 
        if region == "twn":
            groups += twn_group_13 + twn_group_1 + twn_group_2 + twn_group_8 
        if region == "asi":
            groups += asi_group_13 + asi_group_1 + asi_group_8 
        if region == "usa":
            groups += usa_group_13 + usa_group_1 + usa_group_2 + usa_group_3 + usa_group_4 + usa_group_8 + group_3 
            groups += usa_group_5 + usa_group_6 + usa_group_7
        if region == "hkg":
            groups += hkg_group_13 + hkg_group_1 + hkg_group_2 + hkg_group_8
        if region == "kor":
            groups += kor_group_13 + kor_group_1 + kor_group_2 + kor_group_8
        if region == "eur": 
            groups += eur_group_13 + eur_group_1 + eur_group_2 + eur_group_3 + eur_group_8 +  eur_group_7 + group_3 
        if region == "glb":
            groups += glb_group_13 + glb_group_8 + glb_group_3 + glb_group_1 + glb_group_7 + group_3
        if region == "amr":
            groups += amr_group_3 + amr_group_13
        if region == "jpn":
            groups += jpn_group_1 + jpn_group_2 + jpn_group_13 + jpn_group_8
            
        for group in groups:
            if op.startswith("group_vector"):
                for vector in vectors:
                    alpha = "%s(%s,%s,densify(%s))"%(op, field, vector, group)
                    output.append(alpha)
            elif op.startswith("group_percentage"):
                alpha = "%s(%s,densify(%s),percentage=0.5)"%(op, field, group)
                output.append(alpha)
            else:
                alpha = "%s(%s,densify(%s))"%(op, field, group)
                output.append(alpha)
        
        return output

    def load_task_pool(self, alpha_list: list, batch_size: int = 10, concurrent_batches: int = 10) -> list:
        """Split alpha list into pools of batches for concurrent processing."""
        pools = []
        current_pool = []
        current_batch = []
        
        for alpha in alpha_list:
            current_batch.append(alpha)
            
            if len(current_batch) >= batch_size:
                current_pool.append(current_batch)
                current_batch = []
                
                if len(current_pool) >= concurrent_batches:
                    pools.append(current_pool)
                    current_pool = []
        
        # Add any remaining batches
        if current_batch:
            current_pool.append(current_batch)
        if current_pool:
            pools.append(current_pool)
        
        logging.info(f"Created {len(pools)} pools with {batch_size} alphas per batch")
        return pools
