import React from "react";

interface InputProps {
  type?: string;
  placeholder?: string;
  value: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  className?: string;
}

export function Input({
  type = "text",
  placeholder = "",
  value,
  onChange,
  className = "",
}: InputProps) {
  return (
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      className={`border rounded-md px-3 py-2 w-full ${className}`}
    />
  );
}
