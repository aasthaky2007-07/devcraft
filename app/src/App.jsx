import { useEffect, useState } from "react";
import "./App.css";

const domains = ["Electrician", "Tailor", "Tiffin", "Baker"];

function App() {
  const [message, setMessage] = useState("");
  const [domain, setDomain] = useState("Electrician");
  const [showForm, setShowForm] = useState(false);
  const [isParsing, setIsParsing] = useState(false);

  const [orders, setOrders] = useState(() => {
    try {
      const savedOrders = localStorage.getItem("devcraft_orders");
      return savedOrders ? JSON.parse(savedOrders) : [];
    } catch {
      return [];
    }
  });

  // Save orders locally
  useEffect(() => {
    localStorage.setItem(
      "devcraft_orders",
      JSON.stringify(orders)
    );
  }, [orders]);

  // --------------------------------
  // Parse using Python API
  // --------------------------------

  const parseOrder = async () => {
    if (!message.trim() || isParsing) return;

    setIsParsing(true);

    try {
      const response = await fetch(
        "http://localhost:8000/parse",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: message,
            domain: domain,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Parser API failed");
      }

      const parsed = await response.json();

      const newOrder = {
        id: Date.now(),
        customer: parsed.customer || "New Customer",
        domain: domain,
        message: message,
        status: "Pending",
        synced: true,

        parsedItems: parsed.items || [],

        dueDate: parsed.due_date || null,
        amount: parsed.amount ?? null,
        referencesPriorOrder:
          parsed.references_prior_order || false,

        confidence: parsed.confidence ?? 0.8,
        needsClarification:
          parsed.needs_clarification || false,
      };

      setOrders((oldOrders) => [
        newOrder,
        ...oldOrders,
      ]);

      setMessage("");
      setShowForm(false);
    } catch (error) {
      console.log("Parser unavailable:", error);

      // Offline fallback
      const offlineOrder = {
        id: Date.now(),
        customer: "New Customer",
        domain: domain,
        message: message,
        status: "Pending",
        synced: false,

        parsedItems: [],

        dueDate: null,
        amount: null,
        referencesPriorOrder: false,

        confidence: 0,
        needsClarification: true,
      };

      setOrders((oldOrders) => [
        offlineOrder,
        ...oldOrders,
      ]);

      setMessage("");
      setShowForm(false);
    } finally {
      setIsParsing(false);
    }
  };

  // --------------------------------
  // Delete order
  // --------------------------------

  const deleteOrder = (id) => {
    setOrders((oldOrders) =>
      oldOrders.filter((order) => order.id !== id)
    );
  };

  return (
    <div className="app">

      {/* HEADER */}
      <header className="header">
        <div>
          <h1>DevCraft</h1>
          <p>Offline-first Order Management</p>
        </div>

        <div className="connection">
          <span className="status-dot"></span>
          Offline Ready
        </div>
      </header>

      <main className="container">

        {/* HERO */}
        <section className="hero">
          <div>
            <h2>Business Orders</h2>

            <p>
              Turn everyday customer messages into
              structured orders — even without internet.
            </p>

            {/* DOMAINS */}
            <div className="domains">
              {domains.map((item) => (
                <button
                  key={item}
                  className={`domain-btn ${
                    domain === item ? "active" : ""
                  }`}
                  onClick={() => setDomain(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          <button
            className="primary-btn"
            onClick={() => setShowForm(!showForm)}
          >
            + New Order
          </button>
        </section>

        {/* CREATE ORDER */}
        {showForm && (
          <section className="order-form">

            <h3>Create Order</h3>

            <label>
              Customer Message
            </label>

            <textarea
              value={message}
              onChange={(e) =>
                setMessage(e.target.value)
              }
              placeholder="Example: 2 kurta chahiye navy blue, chest 40..."
            />

            <div className="form-actions">

              <button
                className="secondary-btn"
                onClick={() => {
                  setMessage("");
                  setShowForm(false);
                }}
              >
                Cancel
              </button>

              <button
                className="primary-btn"
                onClick={parseOrder}
                disabled={isParsing}
              >
                {isParsing
                  ? "Parsing..."
                  : "✨ Parse & Save"}
              </button>

            </div>

          </section>
        )}

        {/* STATS */}
        <section className="stats">

          <div className="stat-card">
            <span>Total Orders</span>
            <strong>{orders.length}</strong>
          </div>

          <div className="stat-card">
            <span>Pending</span>
            <strong>
              {
                orders.filter(
                  (order) =>
                    order.status === "Pending"
                ).length
              }
            </strong>
          </div>

          <div className="stat-card">
            <span>Offline Changes</span>
            <strong>
              {
                orders.filter(
                  (order) => !order.synced
                ).length
              }
            </strong>
          </div>

        </section>

        {/* RECENT ORDERS */}
        <section className="orders-section">

          <div className="section-heading">
            <h2>Recent Orders</h2>
            <span>
              {orders.length} orders
            </span>
          </div>

          {orders.length === 0 ? (

            <div className="empty-state">

              <div className="empty-icon">
                📦
              </div>

              <h3>No orders yet</h3>

              <p>
                Create your first order from a
                customer message.
              </p>

              <button
                className="primary-btn"
                onClick={() =>
                  setShowForm(true)
                }
              >
                Create First Order
              </button>

            </div>

          ) : (

            <div className="orders-list">

              {orders.map((order) => (

                <div
                  className="order-card"
                  key={order.id}
                >

                  {/* ORDER HEADER */}
                  <div className="order-top">

                    <div>
                      <h3>
                        {order.customer}
                      </h3>

                      <span className="order-id">
                        Order #{order.id}
                      </span>
                    </div>

                    <span className="badge">
                      {order.status}
                    </span>

                  </div>

                  {/* DOMAIN */}
                  <p>
                    <strong>Domain:</strong>{" "}
                    {order.domain}
                  </p>

                  {/* CUSTOMER MESSAGE */}
                  <div className="message-box">

                    <strong>
                      Customer Message
                    </strong>

                    <p className="message">
                      {order.message}
                    </p>

                  </div>

                  {/* PARSED RESULT */}
                  {order.parsedItems &&
                    order.parsedItems.length > 0 && (

                    <div className="parsed-result">

                      <h3>
                        ✨ Parsed Order
                      </h3>

                      {order.parsedItems.map(
                        (item, index) => (

                          <div
                            className="parsed-item"
                            key={index}
                          >

                            <div className="parsed-item-top">

                              <strong>
                                {item.description}
                              </strong>

                              <span>
                                × {item.quantity}
                              </span>

                            </div>

                            {item.attributes &&
                              Object.entries(
                                item.attributes
                              ).map(
                                ([key, value]) => (

                                  <div
                                    className="attribute"
                                    key={key}
                                  >

                                    <span>
                                      {key}
                                    </span>

                                    <strong>
                                      {String(value)}
                                    </strong>

                                  </div>

                                )
                              )}

                          </div>

                        )
                      )}

                      {order.dueDate && (
                        <div className="attribute">
                          <span>Due date</span>
                          <strong>
                            {order.dueDate}
                          </strong>
                        </div>
                      )}

                      {order.amount !== null &&
                        order.amount !== undefined && (
                        <div className="attribute">
                          <span>Amount</span>
                          <strong>
                            ₹{order.amount}
                          </strong>
                        </div>
                      )}

                      {order.needsClarification && (
                        <div className="clarification">
                          ⚠️ Needs clarification
                        </div>
                      )}

                    </div>
                  )}

                  {/* OFFLINE / SYNC */}
                  <div className="order-footer">

                    <span>
                      {order.synced
                        ? "✓ Parsed & Saved"
                        : "● Saved Offline"}
                    </span>

                    <button
                      className="delete-btn"
                      onClick={() =>
                        deleteOrder(order.id)
                      }
                    >
                      Delete
                    </button>

                  </div>

                </div>

              ))}

            </div>

          )}

        </section>

      </main>
    </div>
  );
}

export default App;