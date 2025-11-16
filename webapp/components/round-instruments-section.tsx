"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Plus,
  Pencil,
  Trash2,
  User,
  Building2,
  DollarSign,
  Percent,
  Calendar,
  TrendingUp,
  FileText,
  Clock,
  Shield,
  Target,
  ChevronDown,
} from "lucide-react";
import type { Round, Instrument, CalculationType } from "@/types/cap-table";
import type { RoundValidation } from "@/lib/validation";
import { getFieldError } from "@/lib/validation";
import {
  formatCurrency,
  formatNumber,
  decimalToPercentage,
} from "@/lib/formatters";
import {
  ColumnDef,
  ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
  VisibilityState,
} from "@tanstack/react-table";

// Extend ColumnMeta to include sticky property
declare module "@tanstack/react-table" {
  interface ColumnMeta<TData, TValue> {
    sticky?: boolean;
  }
}
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface RoundInstrumentsSectionProps {
  round: Round;
  calculationType: CalculationType;
  regularInstruments: Instrument[];
  validation?: RoundValidation;
  onAddInstrument: () => void;
  onEditInstrument: (instrument: Instrument, index: number) => void;
  onDeleteInstrument: (index: number) => void;
}

type InstrumentRow = Instrument & {
  displayIndex: number;
  actualIndex: number;
  hasError: boolean;
};

export function RoundInstrumentsSection({
  round,
  calculationType,
  regularInstruments,
  validation,
  onAddInstrument,
  onEditInstrument,
  onDeleteInstrument,
}: RoundInstrumentsSectionProps) {
  const instrumentsError = getFieldError(
    validation?.errors ?? [],
    "instruments"
  );
  const proRataInstruments = round.instruments.filter(
    (inst) => "pro_rata_type" in inst
  );
  const hasAnyInstruments =
    regularInstruments.length > 0 || proRataInstruments.length > 0;

  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [isScrollable, setIsScrollable] = React.useState(false);
  const tableContainerRef = React.useRef<HTMLDivElement>(null);

  const getInstrumentFieldValue = (
    instrument: Instrument,
    field: string
  ): string | React.ReactNode => {
    if (field === "holder_name") {
      return "holder_name" in instrument ? instrument.holder_name : "—";
    }
    if (field === "class_name") {
      return "class_name" in instrument ? instrument.class_name : "—";
    }
    if (field === "initial_quantity") {
      return "initial_quantity" in instrument
        ? formatNumber(instrument.initial_quantity)
        : "—";
    }
    if (field === "target_percentage") {
      return "target_percentage" in instrument
        ? `${decimalToPercentage(instrument.target_percentage).toFixed(2)}%`
        : "—";
    }
    if (field === "investment_amount") {
      return "investment_amount" in instrument
        ? formatCurrency(instrument.investment_amount)
        : "—";
    }
    if (field === "interest_rate") {
      return "interest_rate" in instrument
        ? `${decimalToPercentage(instrument.interest_rate).toFixed(2)}%`
        : "—";
    }
    if (field === "payment_date") {
      return "payment_date" in instrument && instrument.payment_date
        ? new Date(instrument.payment_date).toLocaleDateString()
        : "—";
    }
    if (field === "expected_conversion_date") {
      return "expected_conversion_date" in instrument &&
        instrument.expected_conversion_date
        ? new Date(instrument.expected_conversion_date).toLocaleDateString()
        : "—";
    }
    if (field === "interest_type") {
      if ("interest_type" in instrument) {
        const type = instrument.interest_type;
        const labels: Record<string, string> = {
          simple: "Simple",
          compound_yearly: "Compound Yearly",
          compound_monthly: "Compound Monthly",
          compound_daily: "Compound Daily",
          no_interest: "No Interest",
        };
        return labels[type] || type;
      }
      return "—";
    }
    if (field === "discount_rate") {
      return "discount_rate" in instrument
        ? `${decimalToPercentage(instrument.discount_rate).toFixed(2)}%`
        : "—";
    }
    if (field === "valuation_cap") {
      return "valuation_cap" in instrument && instrument.valuation_cap
        ? formatCurrency(instrument.valuation_cap)
        : "—";
    }
    if (field === "valuation_cap_type") {
      if ("valuation_cap_type" in instrument && instrument.valuation_cap_type) {
        const type = instrument.valuation_cap_type;
        const labels: Record<string, string> = {
          default: "Default",
          pre_conversion: "Pre-Conversion",
          post_conversion_own: "Post-Conversion (Own)",
          post_conversion_total: "Post-Conversion (Total)",
        };
        return labels[type] || type;
      }
      return "—";
    }
    if (field === "pro_rata_rights") {
      if ("pro_rata_rights" in instrument && instrument.pro_rata_rights) {
        const rights = instrument.pro_rata_rights;
        return (
          <Badge
            variant={rights === "super" ? "default" : "secondary"}
            className="text-xs"
          >
            {rights === "super" ? "Super" : "Standard"}
          </Badge>
        );
      }
      return <span className="text-muted-foreground text-sm">None</span>;
    }
    if (field === "pro_rata_percentage") {
      return "pro_rata_percentage" in instrument &&
        instrument.pro_rata_percentage !== undefined
        ? `${decimalToPercentage(instrument.pro_rata_percentage).toFixed(2)}%`
        : "—";
    }
    return "—";
  };

  // Prepare data for table
  const tableData: InstrumentRow[] = React.useMemo(() => {
    return regularInstruments.map((instrument, displayIndex) => {
      const actualIndex = round.instruments.findIndex(
        (inst) => inst === instrument
      );
      const hasError = !!getFieldError(
        validation?.errors ?? [],
        `instruments[${actualIndex}]`
      );
      return {
        ...instrument,
        displayIndex,
        actualIndex,
        hasError,
      };
    });
  }, [regularInstruments, round.instruments, validation?.errors]);

  // Define columns based on calculation type
  const columns = React.useMemo<ColumnDef<InstrumentRow>[]>(() => {
    const baseColumns: ColumnDef<InstrumentRow>[] = [
      {
        id: "index",
        header: "#",
        cell: ({ row }) => (
          <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary/10 text-primary font-semibold text-xs">
            {row.original.displayIndex + 1}
          </div>
        ),
        enableSorting: false,
        enableHiding: false,
      },
      {
        accessorKey: "holder_name",
        header: ({ column }) => {
          return (
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="h-auto p-0 hover:bg-transparent"
            >
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <User className="h-3.5 w-3.5 text-muted-foreground" />
                Holder
              </div>
            </Button>
          );
        },
        cell: ({ row }) => {
          const holderName =
            "holder_name" in row.original ? row.original.holder_name : "—";
          return (
            <div className="flex items-center gap-2">
              <span className="font-medium">{holderName}</span>
              {row.original.hasError && (
                <Badge variant="destructive" className="text-xs">
                  Error
                </Badge>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: "class_name",
        header: ({ column }) => {
          return (
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="h-auto p-0 hover:bg-transparent"
            >
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
                Class
              </div>
            </Button>
          );
        },
        cell: ({ row }) => (
          <span className="text-sm text-muted-foreground">
            {getInstrumentFieldValue(row.original, "class_name") as string}
          </span>
        ),
      },
    ];

    switch (calculationType) {
      case "fixed_shares":
        return [
          ...baseColumns,
          {
            accessorKey: "initial_quantity",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                Shares
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "initial_quantity")}
              </span>
            ),
          },
          {
            accessorKey: "pro_rata_rights",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Shield className="h-3.5 w-3.5 text-muted-foreground" />
                Pro-Rata Rights
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "pro_rata_rights")}
              </span>
            ),
          },
          {
            accessorKey: "pro_rata_percentage",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Percent className="h-3.5 w-3.5 text-muted-foreground" />
                Pro-Rata
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "pro_rata_percentage")}
              </span>
            ),
          },
        ];
      case "target_percentage":
        return [
          ...baseColumns,
          {
            accessorKey: "target_percentage",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Target className="h-3.5 w-3.5 text-muted-foreground" />
                Target %
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "target_percentage")}
              </span>
            ),
          },
          {
            accessorKey: "pro_rata_rights",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Shield className="h-3.5 w-3.5 text-muted-foreground" />
                Pro-Rata Rights
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "pro_rata_rights")}
              </span>
            ),
          },
          {
            accessorKey: "pro_rata_percentage",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Percent className="h-3.5 w-3.5 text-muted-foreground" />
                Pro-Rata %
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "pro_rata_percentage")}
              </span>
            ),
          },
        ];
      case "valuation_based":
        return [
          ...baseColumns,
          {
            accessorKey: "investment_amount",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <DollarSign className="h-3.5 w-3.5 text-muted-foreground" />
                Investment
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "investment_amount")}
              </span>
            ),
          },
          {
            accessorKey: "pro_rata_rights",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Shield className="h-3.5 w-3.5 text-muted-foreground" />
                Pro-Rata Rights
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "pro_rata_rights")}
              </span>
            ),
          },
          {
            accessorKey: "pro_rata_percentage",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Percent className="h-3.5 w-3.5 text-muted-foreground" />
                Pro-Rata %
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "pro_rata_percentage")}
              </span>
            ),
          },
        ];
      case "convertible":
        return [
          ...baseColumns,
          {
            accessorKey: "investment_amount",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <DollarSign className="h-3.5 w-3.5 text-muted-foreground" />
                Investment
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "investment_amount")}
              </span>
            ),
          },
          {
            accessorKey: "interest_rate",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Percent className="h-3.5 w-3.5 text-muted-foreground" />
                Interest Rate
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "interest_rate")}
              </span>
            ),
          },
          {
            accessorKey: "payment_date",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                Payment Date
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "payment_date")}
              </span>
            ),
          },
          {
            accessorKey: "expected_conversion_date",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                Conversion Date
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(
                  row.original,
                  "expected_conversion_date"
                )}
              </span>
            ),
          },
          {
            accessorKey: "interest_type",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                Interest Type
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "interest_type")}
              </span>
            ),
          },
          {
            accessorKey: "discount_rate",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <TrendingUp className="h-3.5 w-3.5 text-muted-foreground" />
                Discount
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "discount_rate")}
              </span>
            ),
          },
          {
            accessorKey: "valuation_cap",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <DollarSign className="h-3.5 w-3.5 text-muted-foreground" />
                Valuation Cap
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "valuation_cap")}
              </span>
            ),
          },
          {
            accessorKey: "valuation_cap_type",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                Cap Type
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "valuation_cap_type")}
              </span>
            ),
          },
          {
            accessorKey: "pro_rata_rights",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Shield className="h-3.5 w-3.5 text-muted-foreground" />
                Pro-Rata Rights
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "pro_rata_rights")}
              </span>
            ),
          },
          {
            accessorKey: "pro_rata_percentage",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Percent className="h-3.5 w-3.5 text-muted-foreground" />
                Pro-Rata %
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "pro_rata_percentage")}
              </span>
            ),
          },
        ];
      case "safe":
        return [
          ...baseColumns,
          {
            accessorKey: "investment_amount",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <DollarSign className="h-3.5 w-3.5 text-muted-foreground" />
                Investment
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "investment_amount")}
              </span>
            ),
          },
          {
            accessorKey: "expected_conversion_date",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                Conversion Date
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(
                  row.original,
                  "expected_conversion_date"
                )}
              </span>
            ),
          },
          {
            accessorKey: "discount_rate",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <TrendingUp className="h-3.5 w-3.5 text-muted-foreground" />
                Discount
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "discount_rate")}
              </span>
            ),
          },
          {
            accessorKey: "valuation_cap",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <DollarSign className="h-3.5 w-3.5 text-muted-foreground" />
                Valuation Cap
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "valuation_cap")}
              </span>
            ),
          },
          {
            accessorKey: "valuation_cap_type",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                Cap Type
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "valuation_cap_type")}
              </span>
            ),
          },
          {
            accessorKey: "pro_rata_rights",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Shield className="h-3.5 w-3.5 text-muted-foreground" />
                Pro-Rata Rights
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "pro_rata_rights")}
              </span>
            ),
          },
          {
            accessorKey: "pro_rata_percentage",
            header: () => (
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Percent className="h-3.5 w-3.5 text-muted-foreground" />
                Pro-Rata %
              </div>
            ),
            cell: ({ row }) => (
              <span className="text-sm">
                {getInstrumentFieldValue(row.original, "pro_rata_percentage")}
              </span>
            ),
          },
        ];
      default:
        return baseColumns;
    }
  }, [calculationType]);

  // Add actions column
  const columnsWithActions: ColumnDef<InstrumentRow>[] = React.useMemo(() => {
    return [
      ...columns,
      {
        id: "actions",
        header: () => <div className="text-right">Actions</div>,
        cell: ({ row }) => {
          return (
            <div className="flex items-center justify-end gap-1">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() =>
                  onEditInstrument(row.original, row.original.actualIndex)
                }
                className="h-8 w-8 p-0"
                title="Edit instrument"
              >
                <Pencil className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => onDeleteInstrument(row.original.actualIndex)}
                className="h-8 w-8 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                title="Delete instrument"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          );
        },
        enableSorting: false,
        enableHiding: false,
        meta: {
          sticky: true,
        },
      },
    ];
  }, [columns, onEditInstrument, onDeleteInstrument]);

  const table = useReactTable({
    data: tableData,
    columns: columnsWithActions,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
    },
  });

  // Check if table is scrollable
  React.useEffect(() => {
    const checkScrollable = () => {
      if (tableContainerRef.current) {
        const { scrollWidth, clientWidth } = tableContainerRef.current;
        setIsScrollable(scrollWidth > clientWidth);
      }
    };

    checkScrollable();
    const resizeObserver = new ResizeObserver(checkScrollable);
    if (tableContainerRef.current) {
      resizeObserver.observe(tableContainerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, [tableData, columnVisibility]);

  return (
    <div className="space-y-4">
      {instrumentsError && !hasAnyInstruments && (
        <div className="rounded-md bg-amber-50 dark:bg-amber-950/20 border border-amber-200/50 dark:border-amber-800/50 p-4">
          <p className="text-sm font-medium text-amber-900 dark:text-amber-200">
            {instrumentsError}
          </p>
        </div>
      )}

      {regularInstruments.length === 0 ? (
        <div className="flex items-center justify-start">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onAddInstrument}
            className="font-medium"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Instrument
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onAddInstrument}
              className="font-medium"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Instrument
            </Button>
            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    Columns <ChevronDown className="ml-2 h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {table
                    .getAllColumns()
                    .filter((column) => column.getCanHide())
                    .map((column) => {
                      return (
                        <DropdownMenuCheckboxItem
                          key={column.id}
                          className="capitalize"
                          checked={column.getIsVisible()}
                          onCheckedChange={(value) =>
                            column.toggleVisibility(!!value)
                          }
                        >
                          {column.id}
                        </DropdownMenuCheckboxItem>
                      );
                    })}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
          <div
            ref={tableContainerRef}
            className={`rounded-md border border-border/50 overflow-x-auto w-full relative ${
              isScrollable
                ? "shadow-[inset_-8px_0_8px_-8px_rgba(0,0,0,0.1)] dark:shadow-[inset_-8px_0_8px_-8px_rgba(0,0,0,0.3)]"
                : ""
            }`}
          >
            {isScrollable && (
              <div className="absolute right-0 top-0 bottom-0 w-8 pointer-events-none bg-gradient-to-l from-background to-transparent z-10" />
            )}
            <Table className="min-w-full">
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => {
                      const isSticky = header.column.columnDef.meta?.sticky;
                      return (
                        <TableHead
                          key={header.id}
                          className={`min-w-[120px] whitespace-nowrap ${
                            isSticky
                              ? "sticky right-0 bg-background z-20 border-l border-border/50 shadow-[inset_4px_0_4px_-4px_rgba(0,0,0,0.1)] dark:shadow-[inset_4px_0_4px_-4px_rgba(0,0,0,0.3)]"
                              : ""
                          }`}
                          style={isSticky ? { minWidth: "100px" } : undefined}
                        >
                          {header.isPlaceholder
                            ? null
                            : flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                              )}
                        </TableHead>
                      );
                    })}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.map((row) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                    className={`group ${
                      row.original.hasError
                        ? "bg-destructive/5 hover:bg-destructive/10"
                        : ""
                    }`}
                  >
                    {row.getVisibleCells().map((cell) => {
                      const isSticky = cell.column.columnDef.meta?.sticky;
                      const rowHasError = row.original.hasError;
                      return (
                        <TableCell
                          key={cell.id}
                          className={`min-w-[120px] whitespace-nowrap ${
                            isSticky
                              ? `sticky right-0 z-20 border-l border-border/50 shadow-[inset_4px_0_4px_-4px_rgba(0,0,0,0.1)] dark:shadow-[inset_4px_0_4px_-4px_rgba(0,0,0,0.3)] ${
                                  rowHasError
                                    ? "bg-destructive/5 group-hover:bg-destructive/10"
                                    : "bg-background group-hover:bg-muted/50"
                                }`
                              : ""
                          }`}
                          style={isSticky ? { minWidth: "100px" } : undefined}
                        >
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </div>
  );
}
