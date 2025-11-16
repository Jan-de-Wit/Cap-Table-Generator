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
} from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
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
            <div className="pr-2">
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
            </div>
          );
        },
        enableSorting: false,
        enableHiding: false,
        size: 0,
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
            Pro-Rata Percentage
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
        id: "actions",
        header: () => <div className="text-right">Actions</div>,
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
            <div className="flex items-center justify-end">
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
          sticky: true,
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
                  const isSticky = header.column.columnDef.meta?.sticky;
                  const isCheckbox = header.column.id === "checkbox";
                  const isActions = header.column.id === "actions";
                  return (
                    <TableHead
                      key={header.id}
                      className={`${
                        isCheckbox || isActions ? "" : "min-w-[120px]"
                      } whitespace-nowrap ${
                        isSticky ? "sticky right-0 z-20 p-0 m-0" : ""
                      }`}
                      style={
                        isSticky && !isActions
                          ? {
                              minWidth: "100px",
                            }
                          : undefined
                      }
                    >
                      <div
                        className={`h-full flex items-center relative ${
                          isSticky
                            ? `border-l border-border/50 ${
                                isActions ? "pl-6 pr-4 justify-end" : "px-4"
                              }`
                            : ""
                        }`}
                      >
                        {isSticky && (
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
                        {!isSticky &&
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
                    ? "bg-blue-50 dark:bg-blue-950/30 hover:bg-blue-50 dark:hover:bg-blue-800"
                    : "bg-green-50 dark:bg-green-950/30 hover:bg-green-50 dark:hover:bg-green-800"
                  : "bg-background hover:bg-gray-50 dark:hover:bg-gray-900";
                const stickyBaseBg = isExercised
                  ? isSuper
                    ? "bg-blue-50 dark:bg-blue-950/30"
                    : "bg-green-50 dark:bg-green-950/30"
                  : "bg-background";
                const stickyHoverBg = isExercised
                  ? isSuper
                    ? "group-hover:bg-blue-50 dark:group-hover:bg-blue-800"
                    : "group-hover:bg-green-50 dark:group-hover:bg-green-800"
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
                      const isSticky = cell.column.columnDef.meta?.sticky;
                      const isCheckbox = cell.column.id === "checkbox";
                      const isActions = cell.column.id === "actions";
                      return (
                        <TableCell
                          key={cell.id}
                          className={`${
                            isCheckbox || isActions ? "" : "min-w-[120px]"
                          } whitespace-nowrap ${
                            isSticky
                              ? "sticky right-0 z-20 p-0 m-0"
                              : "py-3"
                          }`}
                          style={
                            isSticky && !isActions
                              ? {
                                  minWidth: "100px",
                                }
                              : undefined
                          }
                        >
                          <div
                            className={`h-full flex items-center ${
                              isSticky
                                ? `border-l border-border/50 py-3 relative ${
                                    isActions ? "pl-6 pr-4 justify-end" : "px-4"
                                  }`
                                : ""
                            }`}
                          >
                            {isSticky && (
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
                            {!isSticky &&
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
