"use client";

import { useState, useEffect } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { Loader } from "lucide-react";
import { MultiSelect } from "../components/ui/multiselect";

// Define types for API responses and state variables
interface Tool {
  name: string;
  summary: string;
  pricing: string;
}

// Define a separate interface for the best tool since it includes a 'reason' property
interface BestTool {
  name: string;
  reason: string;
}

interface AIResponse {
  summary: string;
  best_tool: BestTool | null;
  tools: Tool[];
}

interface FiltersResponse {
  categories: string[];
  pricing: string[];
}

interface PersonaResponse {
  persona: string;
}

interface ClickResponse {
  updated_persona: string;
}

export default function Chatbot() {
  const [query, setQuery] = useState<string>("");
  const [response, setResponse] = useState<AIResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [categories, setCategories] = useState<string[]>([]);
  const [pricing, setPricing] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedPricing, setSelectedPricing] = useState<string[]>([]);
  const [expandedTool, setExpandedTool] = useState<string | null>(null);
  const [persona, setPersona] = useState<string | null>(null);

  // Fetch filter options
  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const res = await fetch("http://127.0.0.1:3001/api/filters");
        const data: FiltersResponse = await res.json();
        setCategories(data.categories || []);
        setPricing(data.pricing || []);
      } catch (error) {
        console.error("Error fetching filter options:", error);
      }
    };

    fetchFilters();
  }, []);

  // Fetch persona
  useEffect(() => {
    const fetchPersona = async () => {
      try {
        const res = await fetch("http://127.0.0.1:3001/api/persona?user_id=guest");
        const data: PersonaResponse = await res.json();
        console.log("Detected persona:", data.persona);
        setPersona(data.persona);
      } catch (error) {
        console.error("Error fetching persona:", error);
      }
    };

    fetchPersona();
  }, []);

  const handleToggle = async (
    setFilter: React.Dispatch<React.SetStateAction<string[]>>,
    filter: string[],
    value: string,
    type: "category" | "pricing"
  ) => {
    const isAdding = !filter.includes(value);

    setFilter((prev) =>
      isAdding ? [...prev, value] : prev.filter((item) => item !== value)
    );

    if (isAdding && type === "category") {
      try {
        const res = await fetch("http://127.0.0.1:3001/api/click", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: "guest", category_name: value }),
        });
        const data: ClickResponse = await res.json();
        console.log("Updated persona after category click:", data.updated_persona);
        setPersona(data.updated_persona);
      } catch (error) {
        console.error("Error updating persona after category click:", error);
      }
    }
  };

  const handleToolClick = async (toolName: string) => {
    try {
      const res = await fetch("http://127.0.0.1:3001/api/click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: "guest", tool_name: toolName }),
      });
      const data: ClickResponse = await res.json();
      console.log("Updated persona after tool click:", data.updated_persona);
      setPersona(data.updated_persona);
    } catch (error) {
      console.error("Error updating persona after tool click:", error);
    }
  };

  const fetchResponse = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResponse(null);

    try {
      const res = await fetch("http://127.0.0.1:3001/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          categories: selectedCategories,
          pricing: selectedPricing,
          user_id: "guest",
        }),
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! Status: ${res.status}`);
      }

      const data: { ai_tool_recommendation: AIResponse; updated_persona: string } = await res.json();
    
      console.log("Updated persona after query:", data.updated_persona);

      setPersona(data.updated_persona);
      setResponse({
        summary: data.ai_tool_recommendation?.summary || "No summary available.",
        best_tool: data.ai_tool_recommendation?.best_tool || null,
        tools: Array.isArray(data.ai_tool_recommendation?.tools) ? data.ai_tool_recommendation.tools : [],
      });
    } catch (error) {
      console.error("Error fetching response:", error);
      setResponse({
        summary: "Error fetching response. Please try again.",
        best_tool: null,
        tools: [],
      });
    }

    setLoading(false);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-purple-600 p-4">
      <Card className="w-full max-w-md p-6 bg-white shadow-xl rounded-2xl border border-gray-200">
        <h1 className="text-2xl font-semibold text-center mb-4 text-gray-900">Oops! All AI – The AI Tool Finder</h1>
        <div className="flex flex-col gap-4">
          <Input
            type="text"
            placeholder="Ask something..."
            value={query}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
            className="border border-gray-300 p-3 rounded-lg shadow-sm"
          />

          <div className="grid grid-cols-2 gap-4">
            <MultiSelect
              options={categories}
              selectedOptions={selectedCategories}
              onChange={(value: string) => handleToggle(setSelectedCategories, selectedCategories, value, "category")}
              title="Categories"
              placeholder="Select categories"
            />
            <MultiSelect
              options={pricing}
              selectedOptions={selectedPricing}
              onChange={(value: string) => handleToggle(setSelectedPricing, selectedPricing, value, "pricing")}
              title="Pricing"
              placeholder="Select pricing"
            />
          </div>

          <Button
            onClick={fetchResponse}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            {loading ? <Loader className="animate-spin" /> : "Ask"}
          </Button>
        </div>

        {response && (
        <CardContent className="mt-4 space-y-4">
          {/* Summary */}
          {response.summary && (
            <div className="p-4 border rounded-lg bg-gray-100 shadow-md">
              <h2 className="text-lg font-semibold text-gray-900">Overview</h2>
              <p className="text-gray-700">{response.summary}</p>
            </div>
          )}

          {/* Best Recommended Tool */}
          {response.best_tool && (
            <div className="p-4 border rounded-lg bg-yellow-100 shadow-md">
              <h2 className="text-lg font-semibold text-yellow-800">Best Recommended Tool</h2>
              <p className="text-gray-900 font-medium">{response.best_tool.name}</p>
              <p className="text-gray-700">{response.best_tool.reason}</p>
            </div>
          )}

          {/* AI Tools List */}
          {response.tools.length > 0 ? (
            response.tools.map((tool, index) => (
              <div
                key={index}
                className={`p-4 border rounded-lg shadow-md cursor-pointer transition-all duration-300 ${
                  expandedTool === tool.name ? "bg-blue-200 border-blue-500" : "bg-white"
                }`}
                onClick={() => {
                  setExpandedTool(expandedTool === tool.name ? null : tool.name);
                  handleToolClick(tool.name);
                }}
              >
                <h2 className={`text-lg font-semibold ${expandedTool === tool.name ? "text-blue-700" : "text-gray-900"}`}>
                  {tool.name}
                </h2>
                {expandedTool === tool.name && <p className="text-gray-700">{tool.summary}</p>}
              </div>
            ))
          ) : !response.best_tool ? ( // Only show "No AI tools found" if both best_tool and tools are missing
            <div className="p-4 border rounded-lg bg-gray-50 shadow-md">
              <p className="text-gray-700">No AI tools found.</p>
            </div>
          ) : null}
        </CardContent>
      )}
      </Card>
    </div>
  );
}
