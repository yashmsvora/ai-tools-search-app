import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

export function Button({ children, onClick, disabled, className }: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2 bg-blue-600 text-white rounded-md disabled:opacity-50 ${className || ""}`}
    >
      {children}
    </button>
  );
}
