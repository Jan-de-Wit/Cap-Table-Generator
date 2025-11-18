import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Standard group order: Founders, ESOP, Noteholders, Investors, then custom groups alphabetically
 */
const STANDARD_GROUP_ORDER = ["Founders", "ESOP", "Noteholders", "Investors"];

/**
 * Sort groups in the specified order:
 * 1. Founders
 * 2. ESOP
 * 3. Noteholders
 * 4. Investors
 * 5. Custom groups (alphabetically)
 * 
 * @param groups Array of group names to sort
 * @returns Sorted array of group names
 */
export function sortGroups(groups: string[]): string[] {
  const standardGroups: string[] = [];
  const customGroups: string[] = [];
  
  // Separate standard and custom groups
  groups.forEach((group) => {
    const index = STANDARD_GROUP_ORDER.indexOf(group);
    if (index !== -1) {
      standardGroups[index] = group;
    } else {
      customGroups.push(group);
    }
  });
  
  // Filter out undefined values from standard groups (in case a standard group wasn't present)
  const orderedStandardGroups = standardGroups.filter((g): g is string => !!g);
  
  // Sort custom groups alphabetically
  customGroups.sort((a, b) => a.localeCompare(b));
  
  // Combine: standard groups in order, then custom groups
  return [...orderedStandardGroups, ...customGroups];
}
