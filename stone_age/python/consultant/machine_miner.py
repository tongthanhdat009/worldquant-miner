import machine_lib as ml
from time import sleep
import time
import logging
import json
import os
from itertools import product
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('machine_mining.log'),
        logging.StreamHandler()
    ]
)

class MachineMiner:
    def __init__(
        self,
        username: str,
        password: str,
        max_alpha_tests: int = 20,
        batch_size: int = 1,
        concurrent_batches: int = 1,
        run_once: bool = True,
        run_duration_seconds: int = 0,
    ):
        self.brain = ml.WorldQuantBrain(username, password)
        self.alpha_bag = []
        self.gold_bag = []
        self.max_alpha_tests = max_alpha_tests
        self.batch_size = batch_size
        self.concurrent_batches = concurrent_batches
        self.run_once = run_once
        self.run_duration_seconds = max(0, run_duration_seconds)
        
    def mine_alphas(self, region="USA", universe="TOP3000"):
        logging.info(f"Starting machine alpha mining for region: {region}, universe: {universe}")
        deadline = None
        if self.run_duration_seconds > 0:
            deadline = time.monotonic() + self.run_duration_seconds
            logging.info(
                "Run duration limit enabled: %.2f minutes",
                self.run_duration_seconds / 60,
            )
        
        while True:
            if self._deadline_reached(deadline):
                logging.info("Run duration reached; stopping mining loop")
                break
            
            try:
                # Get data fields
                logging.info("Fetching data fields...")
                fields_df = self.brain.get_datafields(region=region, universe=universe)
                logging.info(f"Got {len(fields_df)} data fields")
                
                matrix_fields = self.brain.process_datafields(fields_df, "matrix")
                vector_fields = self.brain.process_datafields(fields_df, "vector")
                logging.info(f"Processed {len(matrix_fields)} matrix fields and {len(vector_fields)} vector fields")
                
                # Generate first order alphas
                logging.info("Generating first order alphas...")
                first_order = self.brain.get_first_order(vector_fields + matrix_fields, self.brain.ops_set)
                logging.info(f"Generated {len(first_order)} first order alphas")
                logging.info(f"Sample alphas: {first_order[:3]}")
                
                # Prepare alpha batches
                neutralization = self.brain.default_neutralization
                alpha_list = self._select_untested_alphas(
                    first_order,
                    region=region,
                    universe=universe,
                    delay=1,
                    decay=0,
                    neutralization=neutralization,
                )
                if not alpha_list:
                    logging.info("No untested alpha candidates found; stopping mining loop")
                    break

                pools = self.brain.load_task_pool(
                    alpha_list,
                    self.batch_size,
                    self.concurrent_batches,
                )
                logging.info(f"Created {len(pools)} pools with {len(pools[0]) if pools else 0} tasks each")
                
                if self._deadline_reached(deadline):
                    logging.info("Run duration reached before starting simulations")
                    break
                
                # Run simulations
                logging.info("Starting simulations...")
                simulated_alphas = self.brain.multi_simulate(
                    pools,
                    neutralization,
                    region,
                    universe,
                    0,
                    deadline=deadline,
                )
                
                # Check pass status and save results. This does not submit alphas.
                self._process_results(simulated_alphas)
                
                if self._deadline_reached(deadline):
                    logging.info("Run duration reached after processing results")
                    break
                
                if self.run_once:
                    logging.info("Run-once mode enabled; stopping after one mining cycle")
                    break
                
            except Exception as e:
                logging.error(f"Error in mining loop: {str(e)}")
                if self.run_once or self._deadline_reached(deadline):
                    break
                
                sleep_seconds = self._sleep_seconds_before_retry(deadline, 600)
                if sleep_seconds <= 0:
                    logging.info("Run duration reached while waiting to retry")
                    break
                
                sleep(sleep_seconds)
                if self._deadline_reached(deadline):
                    logging.info("Run duration reached while waiting to retry")
                    break
                
                self.brain.login()
                continue

    @staticmethod
    def _deadline_reached(deadline):
        return deadline is not None and time.monotonic() >= deadline

    @staticmethod
    def _sleep_seconds_before_retry(deadline, default_seconds):
        if deadline is None:
            return default_seconds
        return min(default_seconds, max(0, deadline - time.monotonic()))

    def _select_untested_alphas(
        self,
        alphas,
        region,
        universe,
        delay,
        decay,
        neutralization,
    ):
        tested_signatures, tested_codes_without_settings = self._load_tested_alpha_signatures()
        selected = []
        skipped = 0

        for alpha in alphas:
            code = str(alpha).strip()
            recommended_settings = self.brain.recommend_simulation_settings(code)
            candidate_delay = int(recommended_settings.get("delay", delay))
            candidate_decay = int(recommended_settings.get("decay", decay))
            candidate_neutralization = str(
                recommended_settings.get("neutralization", neutralization)
            )
            signature = self._alpha_signature(
                code,
                region,
                universe,
                candidate_delay,
                candidate_decay,
                candidate_neutralization,
            )
            if signature in tested_signatures or code in tested_codes_without_settings:
                skipped += 1
                continue

            selected.append({
                "code": code,
                "delay": candidate_delay,
                "decay": candidate_decay,
                "neutralization": candidate_neutralization,
                "truncation": recommended_settings.get("truncation"),
            })
            if len(selected) >= self.max_alpha_tests:
                break

        logging.info(
            "Selected %s new alpha candidates; skipped %s previously tested candidates",
            len(selected),
            skipped,
        )
        if len(selected) < self.max_alpha_tests:
            logging.warning(
                "Only found %s untested candidates out of requested %s",
                len(selected),
                self.max_alpha_tests,
            )
        return selected

    @staticmethod
    def _load_tested_alpha_signatures(
        json_path="tested_alphas.json",
        csv_path="tested_alphas.csv",
    ):
        records = []

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                records = loaded
        except (FileNotFoundError, json.JSONDecodeError):
            records = []

        if not records:
            try:
                import csv

                with open(csv_path, "r", newline="", encoding="utf-8") as f:
                    records = list(csv.DictReader(f))
            except FileNotFoundError:
                records = []

        signatures = set()
        codes_without_settings = set()
        for record in records:
            if not isinstance(record, dict):
                continue

            code = str(record.get("code") or "").strip()
            if not code:
                continue

            region = record.get("region")
            universe = record.get("universe")
            delay = record.get("delay")
            decay = record.get("decay")
            neutralization = record.get("neutralization")
            if region and universe and delay is not None and decay is not None and neutralization:
                signatures.add(
                    MachineMiner._alpha_signature(
                        code,
                        region,
                        universe,
                        delay,
                        decay,
                        neutralization,
                    )
                )
            else:
                codes_without_settings.add(code)

        return signatures, codes_without_settings

    @staticmethod
    def _alpha_signature(code, region, universe, delay, decay, neutralization):
        return (
            str(code).strip(),
            str(region or "").upper(),
            str(universe or "").upper(),
            str(delay),
            str(decay),
            str(neutralization or "").upper(),
        )

    def _process_results(self, simulated_alphas):
        if not simulated_alphas:
            logging.info("No simulation results found to check")
            return
        
        completed_count = sum(
            1
            for item in simulated_alphas
            if item.get("alpha_id") and item.get("simulation_status") == "COMPLETE"
        )
        failed_count = len(simulated_alphas) - completed_count
        logging.info(
            "Processing %s simulation results: %s complete, %s failed/incomplete",
            len(simulated_alphas),
            completed_count,
            failed_count,
        )
        tested_alphas = []
        newly_passed = []
        
        for item in simulated_alphas:
            alpha_id = item.get("alpha_id")
            simulation_status = item.get("simulation_status") or item.get("status")
            if not alpha_id or simulation_status != "COMPLETE":
                cacheable_failure = simulation_status in {
                    "ERROR",
                    "WARNING",
                    "FAILED",
                    "FAIL",
                    "INVALID",
                    "COMPLETE_NO_ALPHA_ID",
                    "SKIPPED_INACCESSIBLE_OPERATOR",
                }
                if not cacheable_failure:
                    logging.warning(
                        "Simulation was not cacheable as tested: status=%s error=%s alpha=%s",
                        simulation_status,
                        item.get("simulation_error"),
                        item.get("code"),
                    )
                    continue
                
                record = dict(item)
                record.update({
                    "alpha_id": alpha_id or "",
                    "passed": False,
                    "check_status": "simulation_error",
                    "failed_check_names": [simulation_status or "UNKNOWN"],
                    "failed_check_details": [],
                    "checked_at": int(time.time()),
                })
                tested_alphas.append(record)
                logging.info(
                    "Recorded failed simulation: status=%s error=%s alpha=%s",
                    simulation_status,
                    record.get("simulation_error"),
                    record.get("code"),
                )
                continue
            
            check = self.brain.get_submission_check_result(alpha_id)
            if check.get("status") == "sleep":
                logging.info("Session refresh requested while checking alpha; re-authenticating")
                self.brain.login()
                check = self.brain.get_submission_check_result(alpha_id)
            
            try:
                record = self.brain.get_alpha_record(alpha_id)
            except Exception as e:
                logging.error(f"Could not fetch alpha details for {alpha_id}: {e}")
                record = {"alpha_id": alpha_id}
            record.setdefault("code", item.get("code", ""))
            record.setdefault("region", item.get("region"))
            record.setdefault("universe", item.get("universe"))
            record.setdefault("delay", item.get("delay"))
            record.setdefault("decay", item.get("decay"))
            record.setdefault("neutralization", item.get("neutralization"))
            
            failed_names = [
                failed.get("name", "UNKNOWN")
                for failed in check.get("failed_checks", [])
            ]
            record.update({
                "passed": bool(check.get("passed")),
                "check_status": check.get("status"),
                "failed_check_names": failed_names,
                "failed_check_details": check.get("failed_checks", []),
                "prod_correlation": check.get("prod_correlation"),
                "checks": check.get("checks", []),
                "checked_at": int(time.time()),
                "progress_url": item.get("progress_url"),
                "simulation_status": simulation_status,
                "simulation_error": item.get("simulation_error"),
            })
            tested_alphas.append(record)
            
            if not check.get("passed"):
                logging.info(f"Alpha {alpha_id} did not pass checks: {failed_names}")
                continue
            
            self.gold_bag.append(record)
            newly_passed.append(record)
            logging.info(
                "PASS alpha %s | Sharpe=%s Fitness=%s ProdCorr=%s",
                alpha_id,
                record.get("sharpe"),
                record.get("fitness"),
                record.get("prod_correlation"),
            )
        
        self.brain.save_tested_alphas(tested_alphas)
        self.brain.save_passed_alphas(newly_passed)
        self.save_results()

    def save_results(self):
        timestamp = int(time.time())
        results = {
            "timestamp": timestamp,
            "gold_alphas": self.gold_bag
        }
        
        with open(f'machine_results_{timestamp}.json', 'w') as f:
            json.dump(results, f, indent=2)
        logging.info(f"Results saved to machine_results_{timestamp}.json")

def main():
    # Read credentials from credential.txt
    try:
        with open('credential.txt', 'r') as f:
            credentials = json.load(f)
        username = credentials[0]
        password = credentials[1]
    except (FileNotFoundError, json.JSONDecodeError, IndexError) as e:
        raise ValueError(f"Error reading credentials from credential.txt: {e}")
    
    if not username or not password:
        raise ValueError("Invalid credentials in credential.txt")
        
    max_alpha_tests = int(os.environ.get("MAX_ALPHA_TESTS", "20"))
    batch_size = int(os.environ.get("BATCH_SIZE", "1"))
    concurrent_batches = int(os.environ.get("CONCURRENT_BATCHES", "1"))
    run_duration_seconds = read_run_duration_seconds()
    run_once_default = "0" if run_duration_seconds > 0 else "1"
    run_once = os.environ.get("RUN_ONCE", run_once_default) != "0"
    region = os.environ.get("REGION", "USA")
    universe = os.environ.get("UNIVERSE", "TOP3000")
    
    miner = MachineMiner(
        username,
        password,
        max_alpha_tests=max_alpha_tests,
        batch_size=batch_size,
        concurrent_batches=concurrent_batches,
        run_once=run_once,
        run_duration_seconds=run_duration_seconds,
    )
    miner.mine_alphas(region=region, universe=universe)

def read_run_duration_seconds():
    """Read optional runtime limit from environment variables."""
    seconds = _read_duration_value("RUN_DURATION_SECONDS", 1)
    if seconds:
        return seconds
    
    minutes = _read_duration_value("RUN_DURATION_MINUTES", 60)
    if minutes:
        return minutes
    
    return _read_duration_value("RUN_DURATION_HOURS", 3600)

def _read_duration_value(name, multiplier):
    value = os.environ.get(name)
    if not value:
        return 0
    try:
        return max(0, int(float(value) * multiplier))
    except ValueError:
        raise ValueError(f"{name} must be a number, got: {value}")

if __name__ == "__main__":
    main() 
