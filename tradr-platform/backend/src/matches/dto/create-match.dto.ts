import { IsString, IsNotEmpty } from 'class-validator';

export class CreateMatchDto {
  @IsString()
  @IsNotEmpty()
  mode: string;

  @IsString()
  @IsNotEmpty()
  userId: string;
}
