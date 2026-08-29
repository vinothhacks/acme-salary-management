export type EmployeeListItem = {
  id: number;
  employee_code: string;
  full_name: string;
  email: string;
  country_code: string;
  department_id: number;
  department_name: string;
  job_title: string;
  band: string;
  employment_type: string;
  hire_date: string;
  status: string;
  current_base: string | null;
  current_currency: string | null;
};

export type SalaryOut = {
  id: number;
  base_amount: string;
  bonus_amount: string;
  allowances_amount: string;
  currency: string;
  effective_from: string;
  effective_to: string | null;
  revision_reason: string | null;
};

export type EmployeeDetail = EmployeeListItem & {
  salary_history: SalaryOut[];
};

export type EmployeePage = {
  items: EmployeeListItem[];
  meta: { page: number; page_size: number; total: number };
};

export type BreakdownRow = {
  key: string;
  headcount: number;
  total_usd: string;
  mean_usd: string;
};

export type Summary = {
  headcount: number;
  total_annual_usd: string;
  mean_usd: string;
  median_usd: string;
  by_country: BreakdownRow[];
  by_department: BreakdownRow[];
};

export type Distribution = {
  bucket_size: string;
  buckets: { bucket_usd: string; count: number }[];
};

export type PercentileRow = {
  key: string;
  p10: string;
  p25: string;
  p50: string;
  p75: string;
  p90: string;
  headcount: number;
};

export type Percentiles = {
  by_band: PercentileRow[];
  by_country: PercentileRow[];
};

export type CostTrend = { points: { as_of: string; total_usd: string }[] };

export type ImportResult = {
  created: number;
  revised: number;
  failed: number;
  errors: { row: number; field: string | null; message: string }[];
};

export type Department = { id: number; name: string };
