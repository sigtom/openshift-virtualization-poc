# Case 03 - NOT TESTED. TEMPLATE for the HammerDB TPROC-C driver run (PostgreSQL).
#
# The administrator copies this into the measured VM, replaces every REPLACE_* value,
# and checks each parameter name against the INSTALLED HammerDB version
# (inside hammerdbcli: "print dict" after "dbset db pg" and "dbset bm TPC-C").
# Parameter names have changed between HammerDB releases; treat this as a starting point.
#
# Run (administrator-defined wrapper "poc-db-run", see ADMIN-GUIDE section 8):
#   cd /opt/HammerDB-REPLACE_VERSION && ./hammerdbcli auto /home/cloud-user/tprocc-run.tcl
#
# Keep identical in every phase: warehouses, virtual users, ramp-up, duration.
# HammerDB's own ramp-up is the warm-up, so use the SAME values each time.
# HammerDB prints NOPM (new orders per minute) and TPM. With a time profile it can also log
# response-time percentiles (p95/p99); read them from the output file of the installed version.
dbset db pg
dbset bm TPC-C
diset connection pg_host 127.0.0.1
diset connection pg_port 5432
diset tpcc pg_superuser REPLACE_DB_ADMIN_USER
diset tpcc pg_superuserpass REPLACE_FROM_ADMIN_SECRET_STORE
diset tpcc pg_user REPLACE_DB_TEST_USER
diset tpcc pg_pass REPLACE_FROM_ADMIN_SECRET_STORE
diset tpcc pg_dbase tpcc
diset tpcc pg_count_ware 10
diset tpcc pg_driver timed
diset tpcc pg_rampup 5
diset tpcc pg_duration 15
diset tpcc pg_timeprofile true
diset tpcc pg_allwarehouse true
loadscript
vuset vu 2
vuset logtotemp 1
vuset unique 1
vucreate
vustart
vuwait
vudestroy
exit
