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
  CheckCircle2,
  Pencil,
  Percent,
  Building2,
  User,
  Shield,
  ChevronDown,
} from "lucide-react";
import type { Round, Instrument } from "@/types/cap-table";
import { decimalToPercentage } from "@/lib/formatters";
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

interface ProRataExerciseSectionProps {
  round: Round;
  holdersWithProRataRights: Array<{
    holderName: string;
    type: "standard" | "super";
    class_name: string;
    percentage?: number;
  }>;
  exercisedProRataRights: Set<string>;
  proRataInstruments: Instrument[];
  onToggleExercise: (
    holderName: string,
    proRataType: "standard" | "super",
    class_name: string,
    percentage?: number
  ) => void;
  onEditProRata: (instrument: Instrument, index: number) => void;
}

type ProRataRow = {
  holder_name: string;
  class_name: string;
  pro_rata_type: "standard" | "super";
  pro_rata_percentage?: number;
  isExercised: boolean;
  existingProRata?: Instrument;
  originalData: {
    holderName: string;
    type: "standard" | "super";
    class_name: string;
    percentage?: number;
  };
};

export function ProRataExerciseSection({
  round,
  holdersWithProRataRights,
  exercisedProRataRights,
  proRataInstruments,
  onToggleExercise,
  onEditProRata,
}: ProRataExerciseSectionProps) {
  if (holdersWithProRataRights.length === 0) {
    return null;
  }

  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [isScrollable, setIsScrollable] = React.useState(false);
  const tableContainerRef = React.useRef<HTMLDivElement>(null);

  // Get the actual pro-rata allocation data for display
  const getProRataData = (
    holderName: string,
    defaultType: "standard" | "super"
  ) => {
    const existingProRata = proRataInstruments.find(
      (inst) => "holder_name" in inst && inst.holder_name === holderName
    );

    if (existingProRata && "pro_rata_type" in existingProRata) {
      return {
        holder_name:
          "holder_name" in existingProRata
            ? existingProRata.holder_name
            : holderName,
        class_name:
          "class_name" in existingProRata ? existingProRata.class_name : "",
        pro_rata_type: existingProRata.pro_rata_type,
        pro_rata_percentage:
          "pro_rata_percentage" in existingProRata
            ? existingProRata.pro_rata_percentage
            : undefined,
      };
    }

    // Return the rights data if not exercised
    const rightsData = holdersWithProRataRights.find(
      (r) => r.holderName === holderName
    );
    return {
      holder_name: holderName,
      class_name: rightsData?.class_name || "",
      pro_rata_type: defaultType,
      pro_rata_percentage: rightsData?.percentage,
    };
  };

  // Prepare data for table
  const tableData: ProRataRow[] = React.useMemo(() => {
    return holdersWithProRataRights.map(
      ({ holderName, type, class_name, percentage }) => {
        const isExercised = exercisedProRataRights.has(holderName);
        const existingProRata = proRataInstruments.find(
          (inst) => "holder_name" in inst && inst.holder_name === holderName
        );
        const proRataData = getProRataData(holderName, type);

        return {
          holder_name: proRataData.holder_name,
          class_name: proRataData.class_name,
          pro_rata_type: proRataData.pro_rata_type,
          pro_rata_percentage: proRataData.pro_rata_percentage,
          isExercised,
          existingProRata,
          originalData: { holderName, type, class_name, percentage },
        };
      }
    );
  }, [holdersWithProRataRights, exercisedProRataRights, proRataInstruments]);

  const columns = React.useMemo<ColumnDef<ProRataRow>[]>(
    () => [
      {
        id: "checkbox",
        header: "",
        cell: ({ row }) => {
          const isExercised = row.original.isExercised;
          return (
            <div
              className={`flex items-center justify-center w-5 h-5 rounded border-2 transition-colors ${
                isExercised
                  ? "bg-primary border-primary text-primary-foreground"
                  : "border-muted-foreground/30"
              }`}
            >
              {isExercised && <CheckCircle2 className="h-3.5 w-3.5" />}
            </div>
          );
        },
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
        cell: ({ row }) => (
          <div className="font-medium">{row.original.holder_name}</div>
        ),
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
            {row.original.class_name}
          </span>
        ),
      },
      {
        accessorKey: "pro_rata_type",
        header: () => (
          <div className="flex items-center gap-1.5 whitespace-nowrap">
            <Shield className="h-3.5 w-3.5 text-muted-foreground" />
            Pro-Rata Type
          </div>
        ),
        cell: ({ row }) => {
          const isSuper = row.original.pro_rata_type === "super";
          return (
            <Badge
              variant={isSuper ? "default" : "secondary"}
              className="text-xs"
            >
              {isSuper ? "Super" : "Standard"} Pro-Rata
            </Badge>
          );
        },
      },
      {
        accessorKey: "pro_rata_percentage",
        header: () => (
          <div className="flex items-center gap-1.5 whitespace-nowrap">
            <Percent className="h-3.5 w-3.5 text-muted-foreground" />
            Pro-Rata Percentage
          </div>
        ),
        cell: ({ row }) => {
          const percentage = row.original.pro_rata_percentage;
          return percentage !== undefined ? (
            <span className="font-semibold text-sm">
              {decimalToPercentage(percentage).toFixed(2)}%
            </span>
          ) : (
            <span className="text-muted-foreground text-sm">—</span>
          );
        },
      },
      {
        accessorKey: "isExercised",
        header: "Status",
        cell: ({ row }) => {
          const isExercised = row.original.isExercised;
          return isExercised ? (
            <Badge variant="secondary" className="text-xs">
              Exercised
            </Badge>
          ) : (
            <span className="text-muted-foreground text-sm">Not Exercised</span>
          );
        },
      },
      {
        id: "actions",
        header: () => <div className="text-right">Actions</div>,
        cell: ({ row }) => {
          const { isExercised, existingProRata, originalData } = row.original;
          if (isExercised && existingProRata) {
            return (
              <div className="flex items-center justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    const actualIndex = round.instruments.findIndex(
                      (inst) => inst === existingProRata
                    );
                    onEditProRata(existingProRata, actualIndex);
                  }}
                  title="Edit pro-rata allocation"
                >
                  <Pencil className="h-4 w-4" />
                </Button>
              </div>
            );
          }
          return <span className="text-muted-foreground text-sm">—</span>;
        },
        enableSorting: false,
        enableHiding: false,
        meta: {
          sticky: true,
        },
      },
    ],
    [round.instruments, onEditProRata]
  );

  const table = useReactTable({
    data: tableData,
    columns,
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
      <div className="flex items-center justify-end">
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
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => {
                const { originalData, isExercised } = row.original;
                const isSuper = originalData.type === "super";
                return (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                    className={`group cursor-pointer transition-colors ${
                      isExercised
                        ? isSuper
                          ? "bg-primary/5 hover:bg-primary/10"
                          : "bg-green-500/5 hover:bg-green-500/10"
                        : "hover:bg-muted/50"
                    }`}
                    onClick={() =>
                      onToggleExercise(
                        originalData.holderName,
                        originalData.type,
                        originalData.class_name,
                        originalData.percentage
                      )
                    }
                  >
                    {row.getVisibleCells().map((cell) => {
                      const isSticky = cell.column.columnDef.meta?.sticky;
                      const isExercised = row.original.isExercised;
                      const isSuper =
                        row.original.originalData.type === "super";
                      const bgClass = isExercised
                        ? isSuper
                          ? "bg-primary/5 group-hover:bg-primary/10"
                          : "bg-green-500/5 group-hover:bg-green-500/10"
                        : "bg-background group-hover:bg-muted/50";
                      return (
                        <TableCell
                          key={cell.id}
                          className={`min-w-[120px] whitespace-nowrap ${
                            isSticky
                              ? `sticky right-0 z-20 border-l border-border/50 shadow-[inset_4px_0_4px_-4px_rgba(0,0,0,0.1)] dark:shadow-[inset_4px_0_4px_-4px_rgba(0,0,0,0.3)] ${bgClass}`
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
                );
              })
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
