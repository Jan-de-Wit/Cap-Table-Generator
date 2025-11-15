export type CalculationType = 
  | "fixed_shares"
  | "target_percentage"
  | "valuation_based"
  | "convertible"
  | "safe";

export type ValuationBasis = "pre_money" | "post_money";

export type ProRataType = "standard" | "super";

export type InterestType = 
  | "simple"
  | "compound_yearly"
  | "compound_monthly"
  | "compound_daily"
  | "no_interest";

export interface Holder {
  name: string;
  description?: string;
  group?: string;
}

export interface FixedSharesInstrument {
  holder_name: string;
  class_name: string;
  initial_quantity: number;
  pro_rata_rights?: "standard" | "super";
  pro_rata_percentage?: number;
}

export interface TargetPercentageInstrument {
  holder_name: string;
  class_name: string;
  target_percentage: number;
  pro_rata_rights?: "standard" | "super";
  pro_rata_percentage?: number;
}

export interface ValuationBasedInstrument {
  holder_name: string;
  class_name: string;
  investment_amount: number;
  pro_rata_rights?: "standard" | "super";
  pro_rata_percentage?: number;
}

export interface ConvertibleInstrument {
  holder_name: string;
  class_name: string;
  investment_amount: number;
  interest_rate: number;
  payment_date: string;
  expected_conversion_date: string;
  interest_type: InterestType;
  discount_rate: number;
  valuation_cap?: number;
  valuation_cap_type?: "default" | "pre_conversion" | "post_conversion_own" | "post_conversion_total";
  pro_rata_rights?: "standard" | "super";
  pro_rata_percentage?: number;
}

export interface SafeInstrument {
  holder_name: string;
  class_name: string;
  investment_amount: number;
  expected_conversion_date: string;
  discount_rate: number;
  valuation_cap?: number;
  valuation_cap_type?: "default" | "pre_conversion" | "post_conversion_own" | "post_conversion_total";
  pro_rata_rights?: "standard" | "super";
  pro_rata_percentage?: number;
}

export interface ProRataAllocation {
  holder_name: string;
  class_name: string;
  pro_rata_type: ProRataType;
  pro_rata_percentage?: number;
}

export type Instrument = 
  | FixedSharesInstrument
  | TargetPercentageInstrument
  | ValuationBasedInstrument
  | ConvertibleInstrument
  | SafeInstrument
  | ProRataAllocation;

export interface Round {
  name: string;
  round_date: string;
  calculation_type: CalculationType;
  valuation_basis?: ValuationBasis;
  valuation?: number;
  price_per_share?: number;
  conversion_round_ref?: string;
  instruments: Instrument[];
}

export interface CapTableData {
  schema_version: "2.0";
  holders: Holder[];
  rounds: Round[];
}

