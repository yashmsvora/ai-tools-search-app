import { useState, useRef, useEffect } from "react";
import { Checkbox } from "./checkbox";

interface MultiSelectProps {
  options: string[];
  selectedOptions: string[];
  onChange: (value: string) => void;
  title: string;
  placeholder: string;
}

export function MultiSelect({
  options,
  selectedOptions,
  onChange,
  title,
  placeholder,
}: MultiSelectProps) {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  const toggleDropdown = () => setOpen((prev) => !prev);

  const handleOptionToggle = (value: string) => {
    onChange(value);
  };

  // Close the dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const displayText =
    selectedOptions.length > 0 ? selectedOptions.join(", ") : placeholder;

  return (
    <div className="relative w-full" ref={dropdownRef}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {title}
      </label>
      <button
        type="button"
        onClick={toggleDropdown}
        className="w-full border border-gray-300 rounded-lg p-3 text-left bg-white shadow-sm transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {displayText}
      </button>
      {open && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto transition-all duration-300 ease-in-out">
          {options.map((option) => (
            <div
              key={option}
              className="flex items-center p-3 hover:bg-gray-100 cursor-pointer transition-all duration-200"
              onClick={() => handleOptionToggle(option)}
            >
              <Checkbox
                checked={selectedOptions.includes(option)}
                onCheckedChange={() => handleOptionToggle(option)}
              />
              <span className="ml-2 text-gray-800">{option}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
