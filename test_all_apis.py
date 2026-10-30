"""Comprehensive test suite for all Support Ticket Triage Agent APIs including Auth."""
import sys
import uuid
from fastapi.testclient import TestClient
from app.api import app


def test_apis():
    print("=" * 60)
    print("STARTING API TEST SUITE (WITH AUTHENTICATION)")
    print("=" * 60)

    with TestClient(app) as client:
        # 1. Test Static UI Endpoint (Public)
        print("\n[1/10] Testing GET / (Static Web UI - Public)...")
        r = client.get("/")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert "<title>Support Triage Agent</title>" in r.text
        print("  --> PASS: Web UI loaded successfully.")

        # 2. Test Protected Route without Auth (Expect 401 Unauthorized)
        print("\n[2/10] Testing Protected Routes without Auth (Expect 401)...")
        r = client.get("/metrics")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        r2 = client.get("/tickets")
        assert r2.status_code == 401, f"Expected 401, got {r2.status_code}"
        print("  --> PASS: Unauthenticated access properly rejected with 401.")

        # 3. Test /auth/signup (Create account with email and password)
        print("\n[3/10] Testing POST /auth/signup (Register new user)...")
        unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "SecurePassword123"

        # Test validation on bad email
        bad_r = client.post("/auth/signup", json={"email": "not-an-email", "password": test_password})
        assert bad_r.status_code == 400

        # Test validation on short password
        bad_r2 = client.post("/auth/signup", json={"email": unique_email, "password": "123"})
        assert bad_r2.status_code == 400

        # Successful registration
        r = client.post("/auth/signup", json={"email": unique_email, "password": test_password})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        signup_data = r.json()
        assert "token" in signup_data and signup_data["user"]["email"] == unique_email
        auth_token = signup_data["token"]
        auth_headers = {"Authorization": f"Bearer {auth_token}"}
        print(f"  --> PASS: User registered ({unique_email}) and token issued.")

        # 4. Test duplicate registration (Expect 400)
        print("\n[4/10] Testing POST /auth/signup with existing email...")
        dup_r = client.post("/auth/signup", json={"email": unique_email, "password": test_password})
        assert dup_r.status_code == 400
        print("  --> PASS: Duplicate registration rejected.")

        # 5. Test /auth/login
        print("\n[5/10] Testing POST /auth/login...")
        # Invalid password
        bad_login = client.post("/auth/login", json={"email": unique_email, "password": "WrongPassword!"})
        assert bad_login.status_code == 401

        # Valid login
        login_r = client.post("/auth/login", json={"email": unique_email, "password": test_password})
        assert login_r.status_code == 200
        login_data = login_r.json()
        assert "token" in login_data
        print("  --> PASS: User successfully authenticated via /auth/login.")

        # 6. Test /auth/me
        print("\n[6/10] Testing GET /auth/me...")
        me_r = client.get("/auth/me", headers=auth_headers)
        assert me_r.status_code == 200
        assert me_r.json()["user"]["email"] == unique_email
        print(f"  --> PASS: Current user verified: {me_r.json()['user']['email']}")

        # 7. Test Metrics with Auth
        print("\n[7/10] Testing GET /metrics (Authenticated)...")
        r = client.get("/metrics", headers=auth_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        assert "total" in data and "auto_resolved_pct" in data and "by_status" in data
        print(f"  --> PASS: Metrics returned: total={data['total']}, auto_pct={data['auto_resolved_pct']}%")

        # 8. Test POST /tickets (Auto-resolvable case)
        print("\n[8/10] Testing POST /tickets (How-to / Account Access)...")
        ticket_payload = {
            "customer": unique_email,
            "subject": "How to reset account password",
            "body": "I forgot my password and cannot log into my account. How do I reset it?"
        }
        r = client.post("/tickets", json=ticket_payload, headers=auth_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        ticket_auto = r.json()
        print(f"  --> Created Ticket #{ticket_auto['id']}")
        print(f"      Category: {ticket_auto['category']}, Urgency: {ticket_auto['urgency']}")
        print(f"      Status:   {ticket_auto['status']}")
        assert ticket_auto["status"] in ("auto_resolved", "needs_approval")
        print("  --> PASS: Ticket processed.")

        # 9. Test POST /tickets (Review / Approval case)
        print("\n[9/10] Testing POST /tickets (Refund request) & approval...")
        ticket_payload2 = {
            "customer": "refund_tester@example.com",
            "subject": "Refund requested for order #12345",
            "body": "I would like to request a refund for my order placed 10 days ago."
        }
        r = client.post("/tickets", json=ticket_payload2, headers=auth_headers)
        assert r.status_code == 200
        ticket_approval = r.json()

        approve_payload = {
            "final_reply": "Your refund for order #12345 has been approved."
        }
        r_approve = client.post(
            f"/tickets/{ticket_approval['id']}/approve",
            json=approve_payload,
            headers=auth_headers
        )
        assert r_approve.status_code == 200
        assert r_approve.json().get("ok") is True
        print(f"  --> PASS: Ticket #{ticket_approval['id']} approved.")

        # 10. Test Logout
        print("\n[10/10] Testing POST /auth/logout & session invalidation...")
        r_logout = client.post("/auth/logout", headers=auth_headers)
        assert r_logout.status_code == 200
        # Subsequent requests with old token should now fail with 401
        r_after = client.get("/metrics", headers=auth_headers)
        assert r_after.status_code == 401
        print("  --> PASS: Session invalidated upon logout.")

    print("\n" + "=" * 60)
    print("ALL API & AUTH TESTS COMPLETED AND PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_apis()
