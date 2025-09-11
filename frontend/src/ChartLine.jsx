import React from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";

export default function ChartLine({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis dataKey="time" stroke="#94a3b8" />
        <YAxis allowDecimals={false} stroke="#94a3b8" />
        <Tooltip
          contentStyle={{
            background: "rgba(15,23,42,0.95)",
            border: "1px solid #334155",
            borderRadius: "8px",
            color: "#f8fafc",
          }}
          itemStyle={{ color: "#fefefe", fontWeight: 500 }}
          labelStyle={{ color: "#38bdf8", fontWeight: 600 }}
        />
        <Legend />
        <Line type="monotone" dataKey="count" stroke="#60a5fa" strokeWidth={2} dot={{ fill: "#38bdf8" }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
