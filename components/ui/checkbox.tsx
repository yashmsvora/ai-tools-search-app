"use client";

import React from "react";

interface CheckboxProps {
  checked: boolean;
  onCheckedChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export function Checkbox({ checked, onCheckedChange }: CheckboxProps) {
  return (
    <label className="flex items-center space-x-2 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={onCheckedChange}
        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
      />
      <span className="text-gray-900">{checked ? "✓" : ""}</span>
    </label>
  );
}
