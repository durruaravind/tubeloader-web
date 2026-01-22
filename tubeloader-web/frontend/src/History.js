import { useEffect, useState } from "react";

const API = process.env.REACT_APP_API;

export default function History() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    fetch(`${API}/history`)
      .then(r => r.json())
      .then(d => setItems(d));
  }, []);

  return (
    <div className="min-h-screen bg-slate-100 p-4">
      <div className="max-w-4xl mx-auto bg-white p-4 rounded shadow">
        <h2 className="text-xl font-bold mb-4">Download History</h2>
        <div className="overflow-x-auto">
          <table className="w-full border">
            <thead className="bg-gray-100">
              <tr>
                <th className="p-2 text-left">Title</th>
                <th className="p-2">Format</th>
                <th className="p-2">Time</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i, idx) => (
                <tr key={idx} className="border-t">
                  <td className="p-2">{i.title}</td>
                  <td className="p-2 text-center">{i.format}</td>
                  <td className="p-2 text-center">{i.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
