import React, { useState, useEffect } from "react";
import { CalendarCheck, PhoneCall, RefreshCw, MessageSquare } from "lucide-react";
import { api } from "../services/api";
import { useToast } from "../components/Toast";

export default function Bookings() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const data = await api.getBookings();
      setBookings(data);
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="saas-card">
        <div className="saas-card-header">
          <div className="saas-card-title">
            <CalendarCheck size={18} color="var(--emerald-500)" />
            <span>Scheduled 5-Minute Phone Call Demos (Automated Callback Queue)</span>
          </div>
          <button className="btn btn-outline btn-sm" onClick={fetchBookings}>
            <RefreshCw size={13} />
            <span>Refresh</span>
          </button>
        </div>

        <div className="table-wrap">
          <table className="saas-table">
            <thead>
              <tr>
                <th>Customer Name</th>
                <th>Phone / WhatsApp Number</th>
                <th>Demo Type</th>
                <th>Scheduled Slot & Notes</th>
                <th>Status</th>
                <th>WhatsApp Alert</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    Loading booked demos...
                  </td>
                </tr>
              ) : !bookings.length ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    No phone demos booked yet. Sarah automatically saves booked demos here during customer calls!
                  </td>
                </tr>
              ) : (
                bookings.map((b) => (
                  <tr key={b.id}>
                    <td>
                      <strong>{b.lead?.name || "Customer / Lead"}</strong>
                    </td>
                    <td>
                      <a
                        href={`tel:${b.lead?.phone_number}`}
                        style={{ color: "var(--primary)", fontWeight: 700, textDecoration: "none" }}
                      >
                        {b.lead?.phone_number || "—"}
                      </a>
                    </td>
                    <td>
                      <span className="badge badge-demo">
                        <PhoneCall size={11} />
                        <span>5-Min Phone Call</span>
                      </span>
                    </td>
                    <td style={{ fontWeight: 600, color: "var(--text-main)" }}>{b.notes || "Slot Confirmed"}</td>
                    <td>
                      <span className="badge badge-demo">CONFIRMED</span>
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{ background: "#ecfdf5", color: "#059669", fontWeight: 700 }}
                      >
                        <MessageSquare size={11} />
                        <span>Sent</span>
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
