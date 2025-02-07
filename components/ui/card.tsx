import React, { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className = "" }: CardProps) {
  return (
    <div className={`p-4 shadow-md rounded-lg bg-white ${className}`}>
      {children}
    </div>
  );
}

export function CardContent({ children, className = "" }: CardProps) {
  return (
    <div className={`mt-2 p-4 border rounded-md bg-gray-50 ${className}`}>
      {children}
    </div>
  );
}
