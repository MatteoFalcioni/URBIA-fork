### 5.3 Update Documentation

**Modify** `README.md`:

- Remove Docker setup instructions
- Add production deployment guide (Railway, Modal, AWS)
- Update architecture diagram (remove Docker, add Modal + S3)
- Add environment variables reference for production

**Update** `DB-README.md`:

- Change database examples to use RDS endpoint
- Remove Docker-specific connection instructions

---

## Phase 6: Security, Monitoring & Hardening

**Goal**: Production-grade security, observability, and cost management.

### 6.1 Security Hardening

**Backend security**:

- Enable HTTPS only (enforced by Railway/Vercel)
- Rotate database credentials quarterly
- Use AWS Secrets Manager for sensitive env vars
- Enable RDS encryption at rest
- Restrict RDS security group to backend IP only
- Enable S3 bucket versioning (for artifact recovery)
- Configure S3 bucket policies (deny public access)

**Modal security**:

- Rotate Modal API tokens quarterly
- Use Modal Secrets for all AWS credentials
- Enable Modal function timeout limits (prevent runaway executions)
- Monitor Modal usage for suspicious patterns

### 6.2 Monitoring & Logging

**Backend monitoring**:

- Integrate Sentry for error tracking
- Add structured logging (JSON format)
- Set up uptime monitoring (UptimeRobot, Pingdom)
- Configure Railway logs forwarding to Logtail

**Database monitoring**:

- Enable RDS Enhanced Monitoring
- Set CloudWatch alarms: CPU > 80%, storage < 10% free
- Monitor slow queries (pg_stat_statements)

**Modal monitoring**:

- Track execution times and failures in Modal dashboard
- Set up alerts for high Modal costs
- Monitor workspace volume usage

### 6.3 Cost Optimization

**AWS cost controls**:

- Set billing alerts at $50, $100, $200/month
- Use S3 Lifecycle policies (move old artifacts to Glacier)
- Consider RDS Reserved Instances (1-year commitment) for prod
- Use AWS Cost Explorer to track spending by service

**Modal cost controls**:

- Set per-function timeout limits (prevent infinite loops)
- Monitor CPU/memory usage, optimize image size
- Use Modal's cold start optimization

**Railway cost controls**:

- Monitor usage dashboard
- Scale down backend during off-peak hours (if usage allows)

### 6.4 Backup & Disaster Recovery

**RDS backups**:

- Automated daily backups (7-day retention)
- Manual snapshot before major schema changes
- Test restore process quarterly

**S3 backups**:

- Enable versioning on both buckets
- Configure cross-region replication (optional, for critical data)

**Modal workspace backups**:

- Periodic exports of workspace volume to S3 (cron job)
- Automated backup script:
  ```python
  # backend/scripts/backup_modal_workspace.py
  import modal
  import boto3
  
  volume = modal.Volume.from_name("lg-urban-workspace")
  # Copy volume contents to S3 backup bucket
  ```

