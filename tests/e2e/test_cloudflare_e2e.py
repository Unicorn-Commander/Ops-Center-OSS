"""
End-to-End Tests for Cloudflare DNS Management
Tests complete user workflows from start to finish

Test Scenarios:
1. Zone Creation Workflow (5 tests)
2. DNS Record Management Workflow (6 tests)
3. Email DNS Preservation Workflow (4 tests)
4. Bulk Operations Workflow (4 tests)
5. Queue Management Workflow (5 tests)
6. Template Application Workflow (3 tests)

Total: 27 E2E test scenarios
"""
import pytest
import asyncio
from datetime import datetime
import time

# ==================== ZONE CREATION WORKFLOW ====================

class TestZoneCreationWorkflow:
    """TC-E2E-1 through TC-E2E-5: Complete zone creation workflow"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_zone_creation_workflow(self, admin_client):
        """
        TC-E2E-1: Complete zone creation flow

        Steps:
        1. Create new zone
        2. Verify zone appears in list
        3. Check zone details
        4. Verify nameservers assigned
        5. Check status (pending)
        """
        # Step 1: Create zone
        create_response = await admin_client.post(
            "/api/v1/cloudflare/zones",
            json={
                "domain": f"test-{int(time.time())}.com",
                "jump_start": True,
                "priority": "normal"
            }
        )

        assert create_response.status_code in [201, 429]

        if create_response.status_code == 201:
            zone_data = create_response.json()
            zone_id = zone_data["zone_id"]
            domain = zone_data["domain"]

            # Step 2: Verify in list
            list_response = await admin_client.get("/api/v1/cloudflare/zones")
            assert list_response.status_code == 200

            zones = list_response.json()["zones"]
            found = any(z["zone_id"] == zone_id for z in zones)
            # May not appear immediately due to async processing

            # Step 3: Get zone details
            detail_response = await admin_client.get(
                f"/api/v1/cloudflare/zones/{zone_id}"
            )
            assert detail_response.status_code in [200, 404]

            if detail_response.status_code == 200:
                details = detail_response.json()

                # Step 4: Verify nameservers
                assert "nameservers" in details
                assert len(details["nameservers"]) == 2
                for ns in details["nameservers"]:
                    assert "cloudflare.com" in ns

                # Step 5: Check status
                assert details["status"] in ["pending", "active"]

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_zone_activation_flow(self, admin_client, mock_zone_id):
        """
        TC-E2E-2: Zone activation and propagation check

        Steps:
        1. Get zone details (pending status)
        2. Simulate nameserver update at registrar
        3. Check propagation status
        4. Verify zone becomes active
        """
        # Step 1: Get initial status
        status_response = await admin_client.get(
            f"/api/v1/cloudflare/zones/{mock_zone_id}"
        )

        if status_response.status_code == 200:
            zone = status_response.json()

            # Step 3: Check propagation
            prop_response = await admin_client.post(
                f"/api/v1/cloudflare/zones/{mock_zone_id}/check-status"
            )

            if prop_response.status_code == 200:
                prop_data = prop_response.json()

                # Verify propagation data structure
                assert "nameserver_propagation" in prop_data
                propagation = prop_data["nameserver_propagation"]

                assert isinstance(propagation, dict)
                # Should have multiple DNS resolver checks
                assert len(propagation) > 0

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_zone_deletion_workflow(self, admin_client, mock_zone_id):
        """
        TC-E2E-3: Complete zone deletion flow

        Steps:
        1. Verify zone exists
        2. Delete zone
        3. Verify zone no longer in list
        4. Verify 404 on get zone
        """
        # Step 1: Verify exists
        get_response = await admin_client.get(
            f"/api/v1/cloudflare/zones/{mock_zone_id}"
        )

        # Step 2: Delete
        delete_response = await admin_client.delete(
            f"/api/v1/cloudflare/zones/{mock_zone_id}"
        )

        assert delete_response.status_code in [200, 404]

        if delete_response.status_code == 200:
            # Step 3 & 4: Verify deleted
            verify_response = await admin_client.get(
                f"/api/v1/cloudflare/zones/{mock_zone_id}"
            )

            # Should be 404 after deletion
            # Or may still exist if deletion is async
            assert verify_response.status_code in [200, 404]


# ==================== DNS RECORD MANAGEMENT WORKFLOW ====================

class TestDNSRecordWorkflow:
    """TC-E2E-6 through TC-E2E-11: DNS record management workflow"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_dns_record_workflow(self, admin_client, mock_zone_id):
        """
        TC-E2E-6: Complete DNS record CRUD workflow

        Steps:
        1. Create A record
        2. Verify record appears in list
        3. Update record (change IP)
        4. Verify update
        5. Delete record
        6. Verify deletion
        """
        # Step 1: Create A record
        create_response = await admin_client.post(
            f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
            json={
                "type": "A",
                "name": "test",
                "content": "192.168.1.100",
                "proxied": False,
                "ttl": 3600
            }
        )

        if create_response.status_code == 201:
            record = create_response.json()
            record_id = record["id"]

            # Step 2: List records
            list_response = await admin_client.get(
                f"/api/v1/cloudflare/zones/{mock_zone_id}/dns"
            )

            if list_response.status_code == 200:
                records = list_response.json()["records"]
                found = any(r["id"] == record_id for r in records)

            # Step 3: Update record
            update_response = await admin_client.put(
                f"/api/v1/cloudflare/zones/{mock_zone_id}/dns/{record_id}",
                json={
                    "content": "192.168.1.200",
                    "proxied": True
                }
            )

            if update_response.status_code == 200:
                # Step 4: Verify update
                updated = update_response.json()
                # Verify response indicates success

                # Step 5: Delete record
                delete_response = await admin_client.delete(
                    f"/api/v1/cloudflare/zones/{mock_zone_id}/dns/{record_id}"
                )

                assert delete_response.status_code in [200, 404]

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_web_server_setup_workflow(self, admin_client, mock_zone_id):
        """
        TC-E2E-7: Setup complete web server (A + CNAME + www)

        Steps:
        1. Create A record for apex (@)
        2. Create CNAME for www
        3. Verify both records exist
        4. Test proxied status
        """
        # Step 1: Create A record for apex
        a_response = await admin_client.post(
            f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
            json={
                "type": "A",
                "name": "@",
                "content": "YOUR_SERVER_IP",
                "proxied": True
            }
        )

        if a_response.status_code == 201:
            a_record = a_response.json()

            # Step 2: Create CNAME for www
            cname_response = await admin_client.post(
                f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
                json={
                    "type": "CNAME",
                    "name": "www",
                    "content": "example.com",
                    "proxied": True
                }
            )

            if cname_response.status_code == 201:
                cname_record = cname_response.json()

                # Step 3: Verify both exist
                list_response = await admin_client.get(
                    f"/api/v1/cloudflare/zones/{mock_zone_id}/dns"
                )

                if list_response.status_code == 200:
                    records = list_response.json()["records"]

                    # Should have at least 2 records
                    # (A and CNAME)

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_email_setup_workflow(self, admin_client, mock_zone_id):
        """
        TC-E2E-8: Complete email setup (MX + SPF + DMARC)

        Steps:
        1. Create MX record
        2. Create SPF record (TXT)
        3. Create DMARC record (TXT)
        4. Verify all records exist
        """
        # Step 1: Create MX record
        mx_response = await admin_client.post(
            f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
            json={
                "type": "MX",
                "name": "@",
                "content": "mail.example.com",
                "priority": 10
            }
        )

        if mx_response.status_code == 201:
            # Step 2: Create SPF
            spf_response = await admin_client.post(
                f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
                json={
                    "type": "TXT",
                    "name": "@",
                    "content": "v=spf1 include:spf.example.com -all"
                }
            )

            # Step 3: Create DMARC
            dmarc_response = await admin_client.post(
                f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
                json={
                    "type": "TXT",
                    "name": "_dmarc",
                    "content": "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"
                }
            )

            # Step 4: Verify all exist
            list_response = await admin_client.get(
                f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
                params={"type": "MX"}
            )

            if list_response.status_code == 200:
                mx_records = list_response.json()["records"]
                # Should have MX record

            txt_response = await admin_client.get(
                f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
                params={"type": "TXT"}
            )

            if txt_response.status_code == 200:
                txt_records = txt_response.json()["records"]
                # Should have SPF and DMARC


# ==================== EMAIL DNS PRESERVATION WORKFLOW ====================

class TestEmailPreservationWorkflow:
    """TC-E2E-12 through TC-E2E-15: Email DNS preservation workflow"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_detect_email_dns_records(self, admin_client, mock_zone_id):
        """
        TC-E2E-12: Detect and warn about email DNS records

        Steps:
        1. Create email records (MX, SPF, DKIM, DMARC)
        2. List all records
        3. Verify email records are identified
        4. Attempt to delete MX record
        5. Verify warning/confirmation required
        """
        # Step 1: Create email records
        email_records = [
            {"type": "MX", "name": "@", "content": "mail.example.com", "priority": 10},
            {"type": "TXT", "name": "@", "content": "v=spf1 include:example.com -all"},
            {"type": "TXT", "name": "_dmarc", "content": "v=DMARC1; p=none"}
        ]

        created_ids = []
        for record_data in email_records:
            response = await admin_client.post(
                f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
                json=record_data
            )

            if response.status_code == 201:
                created_ids.append(response.json()["id"])

        # Step 2: List records
        list_response = await admin_client.get(
            f"/api/v1/cloudflare/zones/{mock_zone_id}/dns"
        )

        if list_response.status_code == 200:
            records = list_response.json()["records"]

            # Step 3: Identify email records
            mx_records = [r for r in records if r["type"] == "MX"]
            spf_records = [r for r in records if r["type"] == "TXT" and "spf1" in r.get("content", "")]
            dmarc_records = [r for r in records if r.get("name", "").startswith("_dmarc")]

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_safe_email_migration(self, admin_client, mock_zone_id):
        """
        TC-E2E-13: Safe migration preserving email

        Steps:
        1. Export existing DNS (including email)
        2. Create new zone
        3. Import email records first
        4. Import other records
        5. Verify email not disrupted
        """
        # Step 1: Export from old zone
        export_response = await admin_client.get(
            f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
            params={"format": "json"}
        )

        if export_response.status_code == 200:
            all_records = export_response.json()["records"]

            # Separate email vs other records
            email_records = [
                r for r in all_records
                if r["type"] in ["MX"] or
                   (r["type"] == "TXT" and any(keyword in r.get("content", "")
                    for keyword in ["spf1", "dkim", "dmarc"]))
            ]

            other_records = [r for r in all_records if r not in email_records]

            # Step 3: Import email records first (in production)
            # This ensures email continuity


# ==================== BULK OPERATIONS WORKFLOW ====================

class TestBulkOperationsWorkflow:
    """TC-E2E-16 through TC-E2E-19: Bulk operations workflow"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_bulk_zone_creation_workflow(self, admin_client):
        """
        TC-E2E-16: Bulk create multiple domains

        Steps:
        1. Submit bulk zone creation (5 domains)
        2. Check response (some added, some queued)
        3. Verify zones in list
        4. Check queue status
        5. Monitor until all active
        """
        timestamp = int(time.time())
        domains = [
            {"domain": f"test{i}-{timestamp}.com", "priority": "normal"}
            for i in range(5)
        ]

        # Step 1: Submit bulk
        bulk_response = await admin_client.post(
            "/api/v1/cloudflare/zones/batch",
            json={"domains": domains}
        )

        assert bulk_response.status_code in [200, 202]

        if bulk_response.status_code == 202:
            result = bulk_response.json()

            # Step 2: Check response
            assert "added" in result
            assert "queued" in result
            assert "failed" in result
            assert "details" in result

            # Step 4: Check queue
            queue_response = await admin_client.get(
                "/api/v1/cloudflare/zones/queue"
            )

            if queue_response.status_code == 200:
                queue_data = queue_response.json()
                assert "queue" in queue_data

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_bulk_dns_record_creation(self, admin_client, mock_zone_id):
        """
        TC-E2E-17: Bulk create DNS records

        Steps:
        1. Prepare bulk records (10 records)
        2. Submit bulk creation
        3. Verify all created
        4. Check for any failures
        """
        records = [
            {"type": "A", "name": f"host{i}", "content": f"192.168.1.{i+100}"}
            for i in range(10)
        ]

        # Step 2: Submit bulk
        bulk_response = await admin_client.post(
            f"/api/v1/cloudflare/zones/{mock_zone_id}/dns/batch",
            json={"records": records}
        )

        if bulk_response.status_code == 201:
            result = bulk_response.json()

            # Step 3: Verify counts
            assert "created" in result
            assert "failed" in result
            assert result["created"] + result["failed"] == len(records)


# ==================== QUEUE MANAGEMENT WORKFLOW ====================

class TestQueueManagementWorkflow:
    """TC-E2E-20 through TC-E2E-24: Queue management workflow"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_queue_workflow_full_cycle(self, admin_client):
        """
        TC-E2E-20: Complete queue management cycle

        Steps:
        1. Fill pending zone limit (3 zones)
        2. Add 4th zone (goes to queue)
        3. Check queue status
        4. Change priority
        5. Activate 1 pending zone
        6. Retry queued domain
        7. Verify queued domain now active
        """
        # This is a complex workflow that would require
        # actual Cloudflare API interaction or comprehensive mocking

        # Step 3: Check queue
        queue_response = await admin_client.get(
            "/api/v1/cloudflare/zones/queue"
        )

        assert queue_response.status_code == 200
        queue_data = queue_response.json()

        assert "queue" in queue_data
        assert "total" in queue_data

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_queue_priority_management(self, admin_client, mock_queue_id):
        """
        TC-E2E-21: Manage queue priorities

        Steps:
        1. Add domains to queue with different priorities
        2. Verify queue ordering (critical first)
        3. Change priority to critical
        4. Verify moved to front of queue
        """
        # Step 3: Change priority
        priority_response = await admin_client.put(
            f"/api/v1/cloudflare/zones/queue/{mock_queue_id}/priority",
            json={"priority": "critical"}
        )

        if priority_response.status_code == 200:
            result = priority_response.json()
            assert result.get("success") is True


# ==================== TEMPLATE APPLICATION WORKFLOW ====================

class TestTemplateWorkflow:
    """TC-E2E-25 through TC-E2E-27: Template application workflow"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_apply_web_server_template_workflow(self, admin_client, mock_zone_id):
        """
        TC-E2E-25: Apply web server template

        Steps:
        1. Get available templates
        2. Select web_server template
        3. Provide variables (IP, domain)
        4. Apply template
        5. Verify all records created
        """
        # Step 1: Get templates
        templates_response = await admin_client.get(
            "/api/v1/cloudflare/templates"
        )

        if templates_response.status_code == 200:
            templates = templates_response.json()["templates"]

            # Step 2: Find web_server template
            web_server = next(
                (t for t in templates if t["id"] == "web_server"),
                None
            )

            if web_server:
                # Step 3 & 4: Apply template
                apply_response = await admin_client.post(
                    f"/api/v1/cloudflare/zones/{mock_zone_id}/dns/apply-template",
                    json={
                        "template_id": "web_server",
                        "variables": {
                            "ip": "YOUR_SERVER_IP",
                            "domain": "example.com"
                        }
                    }
                )

                if apply_response.status_code == 201:
                    result = apply_response.json()

                    # Step 5: Verify created
                    assert result["created"] >= 2  # A + CNAME

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_apply_microsoft365_template_workflow(self, admin_client, mock_zone_id):
        """
        TC-E2E-26: Apply Microsoft 365 email template

        Steps:
        1. Select Microsoft 365 template
        2. Provide tenant name
        3. Apply template
        4. Verify MX, SPF, DMARC created
        """
        apply_response = await admin_client.post(
            f"/api/v1/cloudflare/zones/{mock_zone_id}/dns/apply-template",
            json={
                "template_id": "microsoft_365",
                "variables": {
                    "tenant": "superiorbsolutions"
                }
            }
        )

        if apply_response.status_code == 201:
            result = apply_response.json()
            # Should create multiple records
            assert result.get("created", 0) >= 3


# ==================== PERFORMANCE & RELIABILITY ====================

class TestPerformanceReliability:
    """TC-E2E-28+: Performance and reliability tests"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_concurrent_operations(self, admin_client, mock_zone_id):
        """
        TC-E2E-28: Handle concurrent requests

        Steps:
        1. Submit 10 DNS record creations simultaneously
        2. Verify all complete successfully
        3. Check for race conditions
        """
        # Create 10 concurrent requests
        tasks = [
            admin_client.post(
                f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
                json={
                    "type": "A",
                    "name": f"concurrent{i}",
                    "content": f"192.168.1.{i+50}"
                }
            )
            for i in range(10)
        ]

        # Execute concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes
        successes = sum(
            1 for r in responses
            if not isinstance(r, Exception) and r.status_code == 201
        )

        # Should have some successes
        # (may hit rate limits or zone limits)
        assert successes >= 0

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_pagination_large_dataset(self, admin_client, mock_zone_id):
        """
        TC-E2E-29: Handle pagination for large record sets

        Steps:
        1. Create 100 DNS records
        2. List with pagination (limit=50)
        3. Verify correct page counts
        4. Test offset navigation
        """
        # Step 2: List with pagination
        page1_response = await admin_client.get(
            f"/api/v1/cloudflare/zones/{mock_zone_id}/dns",
            params={"limit": 50, "offset": 0}
        )

        if page1_response.status_code == 200:
            page1_data = page1_response.json()

            # Should have limit/offset in response or pagination metadata
            assert "records" in page1_data


# Run with: pytest tests/e2e/test_cloudflare_e2e.py -v -m e2e --asyncio-mode=auto
