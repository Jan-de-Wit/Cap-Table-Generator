"use client";

import * as React from "react";
import { CheckIcon, ChevronsUpDown, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface ComboboxProps {
  options: string[];
  value?: string;
  onValueChange: (value: string) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyText?: string;
  allowCustom?: boolean;
}

export function Combobox({
  options,
  value,
  onValueChange,
  placeholder = "Select option...",
  searchPlaceholder = "Search...",
  emptyText = "No option found.",
  allowCustom = true,
}: ComboboxProps) {
  const [open, setOpen] = React.useState(false);
  const [searchValue, setSearchValue] = React.useState("");

  const filteredOptions = React.useMemo(() => {
    if (!searchValue) return options;
    const lowerSearch = searchValue.toLowerCase();
    return options.filter((opt) => opt.toLowerCase().includes(lowerSearch));
  }, [options, searchValue]);

  const handleSelect = (selectedValue: string) => {
    // CommandItem passes lowercase value, so we need to find the original case
    const originalValue =
      options.find(
        (opt) => opt.toLowerCase() === selectedValue.toLowerCase()
      ) || selectedValue;
    onValueChange(originalValue === value ? "" : originalValue);
    setOpen(false);
    setSearchValue("");
  };

  const handleCustomValue = () => {
    if (searchValue.trim() && allowCustom) {
      onValueChange(searchValue.trim());
      setOpen(false);
      setSearchValue("");
    }
  };

  const handleClear = () => {
    onValueChange("");
    setOpen(false);
    setSearchValue("");
  };

  React.useEffect(() => {
    if (!open) {
      setSearchValue("");
    }
  }, [open]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between cursor-pointer"
        >
          <span className={cn("truncate", !value && "font-normal")}>
            {value || placeholder}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="p-0"
        align="start"
        style={{ width: "var(--radix-popover-trigger-width)" }}
      >
        <Command shouldFilter={false}>
          <CommandInput
            placeholder={searchPlaceholder}
            value={searchValue}
            onValueChange={setSearchValue}
            onKeyDown={(e) => {
              if (e.key === "Enter" && searchValue.trim() && allowCustom) {
                e.preventDefault();
                handleCustomValue();
              }
            }}
          />
          <CommandList>
            {filteredOptions.length === 0 &&
            searchValue.trim() &&
            allowCustom ? (
              <div className="p-2">
                <div className="text-sm text-muted-foreground mb-2 px-2">
                  Press Enter to use "{searchValue}" or click below
                </div>
                <Button
                  variant="ghost"
                  className="w-full justify-start cursor-pointer"
                  onClick={handleCustomValue}
                >
                  Use "{searchValue}"
                </Button>
              </div>
            ) : filteredOptions.length === 0 ? (
              <CommandEmpty>{emptyText}</CommandEmpty>
            ) : null}
            {filteredOptions.length > 0 && (
              <CommandGroup>
                {filteredOptions.map((option) => (
                  <CommandItem
                    key={option}
                    value={option}
                    onSelect={() => handleSelect(option)}
                  >
                    <CheckIcon
                      className={cn(
                        "mr-2 h-4 w-4",
                        value?.toLowerCase() === option.toLowerCase()
                          ? "opacity-100"
                          : "opacity-0"
                      )}
                    />
                    {option}
                  </CommandItem>
                ))}
                {allowCustom &&
                  searchValue.trim() &&
                  !filteredOptions.some(
                    (opt) =>
                      opt.toLowerCase() === searchValue.trim().toLowerCase()
                  ) && (
                    <CommandItem
                      value={searchValue.trim()}
                      onSelect={handleCustomValue}
                      className="border-t"
                    >
                      <CheckIcon className="mr-2 h-4 w-4 opacity-0" />
                      Use "{searchValue.trim()}"
                    </CommandItem>
                  )}
              </CommandGroup>
            )}
            {value && (
              <CommandGroup>
                <CommandItem
                  value="__clear__"
                  onSelect={handleClear}
                  className="text-muted-foreground border-t"
                >
                  <X className="mr-2 h-4 w-4" />
                  Clear selection
                </CommandItem>
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
