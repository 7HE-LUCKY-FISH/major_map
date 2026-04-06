import { useContext, useState } from "react";
import { Link } from "react-router-dom";
import { AuthContext } from "../../utils/AuthContext";
import { CourseContext } from "../../utils/CourseContext";
import "./Account.css";

export default function Account() {
  const { user, authLoading, logout } = useContext(AuthContext);
  const { plannerLoading } = useContext(CourseContext);
  const [error, setError] = useState("");

  const handleLogout = async () => {
    try {
      await logout();
    } catch (err) {
      setError(err.message);
    }
  };

  if (authLoading || plannerLoading) {
    return (
      <div className="account-container">
        <h2>Loading account...</h2>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="account-container">
        <h2>You are not logged in</h2>
        {error && <p className="error">{error}</p>}
        <p>
          <Link to="/login">Login</Link> or <Link to="/register">create an account</Link>.
        </p>
      </div>
    );
  }

  return (
    <div className="account-container">
      <h2>Welcome, {user.username}!</h2>
      {error && <p className="error">{error}</p>}
      <p>Email: {user.email}</p>
      <p>Member since: {new Date(user.created_at).toLocaleDateString()}</p>
      <p> </p>
      <p>Your major, roadmap, and schedule selections are saved to this account.</p>
      <button className="logout-btn" onClick={handleLogout}>
        Logout
      </button>
    </div>
  );
}
