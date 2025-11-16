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
  Pencil,
  Percent,
  Building2,
  User,
  Shield,
  ChevronDown,
  CheckCircle2,
  Minus,
} from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import type { Round, Instrument } from "@/types/cap-table";
import { decimalToPercentage, formatCurrency } from "@/lib/formatters";
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
    sticky?: boolean | "left" | "right";
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
  exercise_type?: "full" | "partial";
  partial_exercise_amount?: number;
  partial_exercise_percentage?: number;
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

  // Ensure Actions column is always visible
  React.useEffect(() => {
    setColumnVisibility((prev) => ({
      ...prev,
      actions: true,
    }));
  }, []);

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

        // Get exercise information from existing pro-rata instrument
        const exerciseType =
          existingProRata && "exercise_type" in existingProRata
            ? (existingProRata as any).exercise_type
            : isExercised
            ? "full"
            : undefined;
        const partialExerciseAmount =
          existingProRata && "partial_exercise_amount" in existingProRata
            ? (existingProRata as any).partial_exercise_amount
            : undefined;
        const partialExercisePercentage =
          existingProRata && "partial_exercise_percentage" in existingProRata
            ? (existingProRata as any).partial_exercise_percentage
            : undefined;

        return {
          holder_name: proRataData.holder_name,
          class_name: proRataData.class_name,
          pro_rata_type: proRataData.pro_rata_type,
          pro_rata_percentage: proRataData.pro_rata_percentage,
          isExercised,
          exercise_type: exerciseType,
          partial_exercise_amount: partialExerciseAmount,
          partial_exercise_percentage: partialExercisePercentage,
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
            <>
              <Checkbox
                checked={isExercised}
                onCheckedChange={() => {
                  const { originalData } = row.original;
                  onToggleExercise(
                    originalData.holderName,
                    originalData.type,
                    originalData.class_name,
                    originalData.percentage
                  );
                }}
                onClick={(e) => e.stopPropagation()}
              />
            </>
          );
        },
        enableSorting: false,
        enableHiding: false,
        size: 0,
        meta: {
          sticky: "left",
        },
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
              className="h-auto p-0 hover:bg-transparent cursor-pointer"
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
              className="h-auto p-0 hover:bg-transparent cursor-pointer"
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
              variant={isSuper ? "default" : "outline"}
              className="text-xs"
            >
              {isSuper ? "Super" : "Standard"}
            </Badge>
          );
        },
      },
      {
        accessorKey: "pro_rata_percentage",
        header: () => (
          <div className="flex items-center gap-1.5 whitespace-nowrap">
            <Percent className="h-3.5 w-3.5 text-muted-foreground" />
            Pro-Rata
          </div>
        ),
        cell: ({ row }) => {
          const percentage = row.original.pro_rata_percentage;
          return percentage !== undefined ? (
            <span className="text-sm">
              {decimalToPercentage(percentage).toFixed(2)}%
            </span>
          ) : (
            <span className="text-muted-foreground text-sm">—</span>
          );
        },
      },
      {
        accessorKey: "exercise_type",
        header: () => (
          <div className="flex items-center gap-1.5 whitespace-nowrap">
            <CheckCircle2 className="h-3.5 w-3.5 text-muted-foreground" />
            Exercise Type
          </div>
        ),
        cell: ({ row }) => {
          const exerciseType = row.original.exercise_type;
          if (!exerciseType) {
            return <span className="text-muted-foreground text-sm">—</span>;
          }
          return (
            <Badge
              variant={exerciseType === "full" ? "default" : "outline"}
              className="text-xs"
            >
              {exerciseType === "full" ? "Full" : "Partial"}
            </Badge>
          );
        },
      },
      {
        accessorKey: "partial_exercise_amount",
        header: () => (
          <div className="flex items-center gap-1.5 whitespace-nowrap">
            <Minus className="h-3.5 w-3.5 text-muted-foreground" />
            Partial Amount
          </div>
        ),
        cell: ({ row }) => {
          const amount = row.original.partial_exercise_amount;
          return amount !== undefined ? (
            <span className="text-sm">{formatCurrency(amount)}</span>
          ) : (
            <span className="text-muted-foreground text-sm">—</span>
          );
        },
      },
      {
        accessorKey: "partial_exercise_percentage",
        header: () => (
          <div className="flex items-center gap-1.5 whitespace-nowrap">
            <Percent className="h-3.5 w-3.5 text-muted-foreground" />
            Partial
          </div>
        ),
        cell: ({ row }) => {
          const percentage = row.original.partial_exercise_percentage;
          return percentage !== undefined ? (
            <span className="text-sm">
              {decimalToPercentage(percentage).toFixed(2)}%
            </span>
          ) : (
            <span className="text-muted-foreground text-sm">—</span>
          );
        },
      },
      {
        id: "actions",
        header: () => <div className="text-left">Actions</div>,
        cell: ({ row }) => {
          const { existingProRata, originalData } = row.original;
          // Find the pro-rata instrument if it exists
          const proRataInstrument =
            existingProRata ||
            proRataInstruments.find(
              (inst) =>
                "holder_name" in inst &&
                inst.holder_name === originalData.holderName
            );

          return (
            <div className="flex items-center justify-start">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-background/80 border border-transparent hover:border-border rounded cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  if (proRataInstrument) {
                    const actualIndex = round.instruments.findIndex(
                      (inst) => inst === proRataInstrument
                    );
                    if (actualIndex !== -1) {
                      onEditProRata(proRataInstrument, actualIndex);
                    }
                  } else {
                    // If no instrument exists, create a new one and edit it
                    // This will be handled by creating a new pro-rata instrument
                    // The parent component should handle this case
                    onEditProRata(
                      {
                        holder_name: originalData.holderName,
                        class_name: originalData.class_name,
                        pro_rata_type: originalData.type,
                        pro_rata_percentage: originalData.percentage,
                        exercise_type: "full",
                      } as Instrument,
                      -1
                    );
                  }
                }}
                title="Edit pro-rata allocation"
              >
                <Pencil className="h-4 w-4" />
              </Button>
            </div>
          );
        },
        enableSorting: false,
        enableHiding: false,
        meta: {
          sticky: "right",
        },
      },
    ],
    [round.instruments, onEditProRata, proRataInstruments]
  );

  const table = useReactTable({
    data: tableData,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: (updater) => {
      setColumnVisibility((prev) => {
        const newVisibility =
          typeof updater === "function" ? updater(prev) : updater;
        // Ensure Actions column is always visible
        return {
          ...newVisibility,
          actions: true,
        };
      });
    },
    state: {
      sorting,
      columnFilters,
      columnVisibility: {
        ...columnVisibility,
        actions: true, // Always keep Actions visible
      },
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
      <div className="flex items-center justify-start">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="cursor-pointer">
              Columns <ChevronDown className="ml-2 h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {table
              .getAllColumns()
              .filter((column) => column.getCanHide())
              .map((column) => {
                // Map column IDs to their header display names
                const headerNameMap: Record<string, string> = {
                  holder_name: "Holder",
                  class_name: "Class",
                  pro_rata_type: "Pro-Rata Type",
                  pro_rata_percentage: "Pro-Rata Percentage",
                  exercise_type: "Exercise Type",
                  partial_exercise_amount: "Partial Amount",
                  partial_exercise_percentage: "Partial %",
                };
                const displayName =
                  headerNameMap[column.id] ||
                  column.id
                    .split("_")
                    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(" ");
                return (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    checked={column.getIsVisible()}
                    onCheckedChange={(value) =>
                      column.toggleVisibility(!!value)
                    }
                  >
                    {displayName}
                  </DropdownMenuCheckboxItem>
                );
              })}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div
        ref={tableContainerRef}
        className={`rounded-md border border-border/50 overflow-x-auto w-full relative`}
      >
        {isScrollable && (
          <div className="absolute right-0 top-0 bottom-0 w-8 pointer-events-none bg-gradient-to-l from-background to-transparent z-10" />
        )}
        <Table className="min-w-full">
          <TableHeader style={{ padding: 0, margin: 0 }}>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id} className="group">
                {headerGroup.headers.map((header) => {
                  const stickyValue = header.column.columnDef.meta?.sticky;
                  const isStickyLeft =
                    stickyValue === "left" ||
                    (stickyValue === true && header.column.id === "checkbox");
                  const isStickyRight =
                    stickyValue === "right" ||
                    (stickyValue === true && header.column.id === "actions");
                  const isCheckbox = header.column.id === "checkbox";
                  const isActions = header.column.id === "actions";
                  return (
                    <TableHead
                      key={header.id}
                      className={`${
                        isCheckbox || isActions ? "" : "min-w-[120px]"
                      } whitespace-nowrap ${
                        isStickyLeft ? "sticky left-0 z-20 p-0 m-0" : ""
                      } ${isStickyRight ? "sticky right-0 z-20 p-0 m-0" : ""}`}
                      style={
                        (isStickyRight || isStickyLeft) &&
                        !isActions &&
                        !isCheckbox
                          ? {
                              minWidth: "100px",
                            }
                          : undefined
                      }
                    >
                      <div
                        className={`h-full flex items-center relative ${
                          isStickyLeft ? `border-r border-border/50 px-4` : ""
                        } ${
                          isStickyRight
                            ? `border-l border-border/50 ${
                                isActions ? "pl-4 pr-4 justify-start" : "px-4"
                              }`
                            : ""
                        }`}
                      >
                        {(isStickyLeft || isStickyRight) && (
                          <>
                            <div className="absolute inset-0 bg-background group-hover:bg-gray-50 dark:group-hover:bg-gray-900 transition-colors" />
                            <div className="relative z-10">
                              {header.isPlaceholder
                                ? null
                                : flexRender(
                                    header.column.columnDef.header,
                                    header.getContext()
                                  )}
                            </div>
                          </>
                        )}
                        {!isStickyLeft &&
                          !isStickyRight &&
                          (header.isPlaceholder
                            ? null
                            : flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                              ))}
                      </div>
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
                const rowBgClass = isExercised
                  ? isSuper
                    ? "bg-green-50 dark:bg-green-950/20 hover:bg-green-100 dark:hover:bg-green-900/30 border-l-2 border-green-400 dark:border-green-500"
                    : "bg-amber-50 dark:bg-amber-950/20 hover:bg-amber-100 dark:hover:bg-amber-900/30 border-l-2 border-amber-400 dark:border-amber-500"
                  : "bg-background hover:bg-gray-50 dark:hover:bg-gray-900";
                const stickyBaseBg = isExercised
                  ? isSuper
                    ? "bg-green-50 dark:bg-green-950/20"
                    : "bg-amber-50 dark:bg-amber-950/20"
                  : "bg-background";
                const stickyHoverBg = isExercised
                  ? isSuper
                    ? "group-hover:bg-green-100 dark:group-hover:bg-green-900/30"
                    : "group-hover:bg-amber-100 dark:group-hover:bg-amber-900/30"
                  : "group-hover:bg-gray-50 dark:group-hover:bg-gray-900";
                return (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                    className={`group cursor-pointer transition-colors py-0 ${rowBgClass}`}
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
                      const stickyValue = cell.column.columnDef.meta?.sticky;
                      const isStickyLeft =
                        stickyValue === "left" ||
                        (stickyValue === true && cell.column.id === "checkbox");
                      const isStickyRight =
                        stickyValue === "right" ||
                        (stickyValue === true && cell.column.id === "actions");
                      const isCheckbox = cell.column.id === "checkbox";
                      const isActions = cell.column.id === "actions";
                      return (
                        <TableCell
                          key={cell.id}
                          className={`${
                            isCheckbox || isActions ? "" : "min-w-[120px]"
                          } whitespace-nowrap ${
                            isStickyLeft ? "sticky left-0 z-20 p-0 m-0" : ""
                          } ${
                            isStickyRight ? "sticky right-0 z-20 p-0 m-0" : ""
                          } ${!isStickyLeft && !isStickyRight ? "py-3" : ""}`}
                          style={
                            (isStickyRight || isStickyLeft) &&
                            !isActions &&
                            !isCheckbox
                              ? {
                                  minWidth: "100px",
                                }
                              : undefined
                          }
                        >
                          <div
                            className={`h-full flex items-center ${
                              isStickyLeft
                                ? `border-r border-border/50 py-3 relative px-4`
                                : ""
                            } ${
                              isStickyRight
                                ? `border-l border-border/50 py-3 relative ${
                                    isActions
                                      ? "pl-2 pr-2 justify-center"
                                      : "px-4"
                                  }`
                                : ""
                            }`}
                          >
                            {(isStickyLeft || isStickyRight) && (
                              <>
                                <div
                                  className={`absolute inset-0 ${stickyBaseBg} ${stickyHoverBg} transition-colors`}
                                />
                                <div className="relative z-10">
                                  {flexRender(
                                    cell.column.columnDef.cell,
                                    cell.getContext()
                                  )}
                                </div>
                              </>
                            )}
                            {!isStickyLeft &&
                              !isStickyRight &&
                              flexRender(
                                cell.column.columnDef.cell,
                                cell.getContext()
                              )}
                          </div>
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
