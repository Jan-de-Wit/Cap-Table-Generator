/**
 * TypeScript types for Cap Table data structures
 */

export interface Company {
  name: string;
  incorporation_date?: string;
  current_date?: string;
  current_pps?: number;
}

export interface Holder {
  holder_id: string;
  name: string;
  type: 'founder' | 'employee' | 'investor' | 'advisor' | 'option_pool';
  email?: string;
}

export interface SecurityClass {
  class_id: string;
  name: string;
  type: 'common' | 'preferred' | 'option' | 'warrant' | 'safe' | 'convertible_note';
  terms_id?: string;
  conversion_ratio?: number;
}

export interface ConvertibleTerms {
  investment_amount: number;
  discount_rate?: number;
  price_cap?: number;
  interest_rate?: number;
  investment_start_date?: string;
  interest_type?: 'simple' | 'compound';
  accrued_interest?: number;
  conversion_shares?: any;
}

export interface Instrument {
  instrument_id: string;
  holder_id: string;
  class_id: string;
  round_id?: string;
  initial_quantity?: number;
  current_quantity?: number;
  strike_price?: number;
  acquisition_price?: number;
  acquisition_date?: string;
  // Valuation-based calculation fields
  investment_amount?: number;
  valuation_basis?: 'pre_money' | 'post_money';
  interest_rate?: number;
  interest_start_date?: string;
  interest_type?: 'simple' | 'compound';
  accrued_interest?: number;
  // Convertible securities
  convertible_terms?: ConvertibleTerms;
  // Vesting
  vesting_terms?: any;
}

export interface Round {
  round_id: string;
  name: string;
  round_date: string;
  investment_amount?: number;
  pre_money_valuation?: number;
  post_money_valuation?: number;
  price_per_share?: number;
  shares_issued?: number;
  pre_round_shares?: number;
}

export interface CapTable {
  schema_version: string;
  company: Company;
  holders: Holder[];
  classes: SecurityClass[];
  instruments: Instrument[];
  rounds?: Round[];
  terms?: any[];
  waterfall_scenarios?: any[];
}

export interface OwnershipItem {
  holder_name: string;
  shares_issued: number;
  percent_issued: number;
  shares_fd: number;
  percent_fd: number;
}

export interface Metrics {
  totals: {
    authorized: number;
    issued: number;
    fullyDiluted: number;
  };
  ownership: OwnershipItem[];
  pool: {
    size: number;
    granted: number;
    remaining: number;
  };
}

export interface DiffItem {
  op: string;
  path: string;
  from?: any;
  to?: any;
  description?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: number;
}

export type ExecutionMode = 'auto' | 'approval';

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, any>;
  status: string; // pending, approved, executing, success, rejected, failed
}

export interface ToolCallProposal {
  toolCall: ToolCall;
  preview?: any;
  validationErrors: string[];
}

export interface ChatStreamEvent {
  event: 'content' | 'tool_proposal' | 'tool_result' | 'cap_table_update' | 'error';
  data: any;
}

