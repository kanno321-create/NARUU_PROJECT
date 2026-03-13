"use client";

interface FilterOption {
  value: string;
  label: string;
}

interface FilterConfig {
  value: string;
  onChange: (value: string) => void;
  options: FilterOption[];
  placeholder: string;
  ariaLabel: string;
}

interface SearchFilterProps {
  searchValue: string;
  onSearch: (value: string) => void;
  placeholder?: string;
  filters?: FilterConfig[];
}

export default function SearchFilter({
  searchValue,
  onSearch,
  placeholder = "검색...",
  filters,
}: SearchFilterProps) {
  return (
    <div className="flex gap-3 mb-4">
      <input
        type="text"
        placeholder={placeholder}
        value={searchValue}
        onChange={(e) => onSearch(e.target.value)}
        aria-label={placeholder}
        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naruu-500 focus:border-naruu-500 outline-none text-sm"
      />
      {filters?.map((filter) => (
        <select
          key={filter.ariaLabel}
          value={filter.value}
          onChange={(e) => filter.onChange(e.target.value)}
          aria-label={filter.ariaLabel}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
        >
          <option value="">{filter.placeholder}</option>
          {filter.options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ))}
    </div>
  );
}
