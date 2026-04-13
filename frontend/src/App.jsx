import { useState } from "react";
import FilterSidebar from "./components/FilterSidebar";
import ChatWindow from "./components/ChatWindow";

export default function App() {
  const [filters, setFilters] = useState({
    phases: [],
    launchYears: [],
    therapeuticAreas: [],
  });
  const [chatInput, setChatInput] = useState("");

  return (
    <div className="flex h-screen bg-white text-gray-900 font-sans">
      <FilterSidebar
        filters={filters}
        onChange={setFilters}
        onChipInsert={(val) => setChatInput((prev) => (prev ? prev + " " + val : val))}
        onScanWithFilters={(query) => setChatInput(query)}
      />
      <ChatWindow filters={filters} input={chatInput} onInputChange={setChatInput} />
    </div>
  );
}
