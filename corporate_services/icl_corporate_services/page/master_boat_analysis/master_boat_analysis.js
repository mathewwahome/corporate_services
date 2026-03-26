frappe.pages["master_boat_analysis"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Master Boat Analysis",
    single_column: true,
  });

  // Toolbar: Refresh button
  page.add_button(
    __("Refresh"),
    function () {
      load_opportunities();
    },
    { icon: "refresh" },
  );

  // Toolbar: Status filter
  page.add_field({
    fieldtype: "Select",
    fieldname: "status_filter",
    label: __("Status"),
    options: "\nOpen\nQuotation\nConverted\nCancelled",
    change: function () {
      load_opportunities();
    },
  });

  $(`<style>
		.sort-th       { cursor: pointer; user-select: none; white-space: nowrap; }
		.sort-th:hover { background-color: #e9ecef !important; }
		.sort-icon     { opacity: 0.4; font-size: 10px; margin-left: 3px; }
		.table-hover tbody tr { cursor: pointer; }
		.stat-card-top-blue   { border-top: 3px solid #0d6efd; }
		.stat-card-top-green  { border-top: 3px solid #198754; }
		.stat-card-top-amber  { border-top: 3px solid #ffc107; }
		.stat-card-top-red    { border-top: 3px solid #dc3545; }
		.stat-value { font-size: 2rem; font-weight: 700; line-height: 1; }
		.font-monospace-bold  { font-family: 'Courier New', monospace; font-weight: 600; }
	</style>`).appendTo("head");


  $(page.body).html(`
		<div class="container-fluid py-4">

			<!-- Stat Cards -->
			<div class="row g-3 mb-4">
				<div class="col-12 col-sm-6 col-xl-3">
					<div class="card h-100 shadow-sm stat-card-top-blue">
						<div class="card-body">
							<p class="text-muted text-uppercase fw-semibold small mb-1">Total Opportunities</p>
							<div class="stat-value text-dark" id="stat-total">-</div>
							<p class="text-muted small mb-0 mt-1">All records</p>
						</div>
					</div>
				</div>
				<div class="col-12 col-sm-6 col-xl-3">
					<div class="card h-100 shadow-sm stat-card-top-green">
						<div class="card-body">
							<p class="text-muted text-uppercase fw-semibold small mb-1">Open</p>
							<div class="stat-value text-dark" id="stat-open">-</div>
							<p class="text-muted small mb-0 mt-1">Active pipeline</p>
						</div>
					</div>
				</div>
				
				<div class="col-12 col-sm-6 col-xl-3">
					<div class="card h-100 shadow-sm stat-card-top-red">
						<div class="card-body">
							<p class="text-muted text-uppercase fw-semibold small mb-1">Converted</p>
							<div class="stat-value text-dark" id="stat-converted">-</div>
							<p class="text-muted small mb-0 mt-1">Won deals</p>
						</div>
					</div>
				</div>
			</div>

			<!-- Table Card -->
			<div class="card shadow-sm">
				<div class="card-header bg-light d-flex align-items-center justify-content-between flex-wrap gap-2 py-3">
					<div class="d-flex align-items-center gap-2">
						<h6 class="mb-0 fw-bold">Opportunities</h6>
						<span class="badge bg-secondary rounded-pill" id="opp-count">0</span>
					</div>
					<input
						type="text"
						id="opp-search"
						class="form-control form-control-sm"
						style="max-width: 240px;"
						placeholder="Search opportunities...">
				</div>
				<div class="card-body p-0" id="opp-table-container">
					<div class="text-center text-muted py-5">
						<div class="spinner-border spinner-border-sm me-2" role="status"></div>
						Loading opportunities...
					</div>
				</div>
			</div>
		</div>
	`);

  let all_data = [];

  // -- Render Table
  function render_table(data) {
    $("#opp-count").text(data.length);

    if (!data.length) {
      $("#opp-table-container").html(`
				<div class="text-center text-muted py-5">
					<div style="font-size:2.5rem;">🚤</div>
					<p class="mt-2 mb-0">No opportunities found.</p>
				</div>
			`);
      return;
    }

    const badge_map = {
      Open: "text-bg-primary",
      Quotation: "text-bg-warning",
      Converted: "text-bg-success",
      Cancelled: "text-bg-danger",
    };

    let rows = data
      .map((d) => {
        let badge_cls = badge_map[d.status] || "text-bg-secondary";

        let amount = d.opportunity_amount
          ? frappe.format(d.opportunity_amount, { fieldtype: "Currency" })
          : "-";

        let date = d.transaction_date
          ? frappe.datetime.str_to_user(d.transaction_date)
          : "-";

        let assignee = "-";
        try {
          assignee = d._assign ? JSON.parse(d._assign)[0] || "-" : "-";
        } catch (e) {}

        return `
				<tr data-name="${d.name}">
					<td class="ps-3">
						<a class="fw-semibold text-decoration-none"
						   href="/app/opportunity/${d.name}"
						   onclick="event.stopPropagation()">
							${frappe.utils.escape_html(d.name)}
						</a>
					</td>
					<td>${frappe.utils.escape_html(d.opportunity_from || "-")}</td>
					<td>${frappe.utils.escape_html(d.party_name || "-")}</td>
					<td>
						<span class="badge rounded-pill ${badge_cls}">
							${frappe.utils.escape_html(d.status || "-")}
						</span>
					</td>
					<td>${frappe.utils.escape_html(d.opportunity_type || "-")}</td>
					<td>${frappe.utils.escape_html(d.sales_stage || "-")}</td>
					<td>${frappe.utils.escape_html(assignee)}</td>
					<td class="text-nowrap text-muted small">${date}</td>
				</tr>
			`;
      })
      .join("");

    $("#opp-table-container").html(`
			<div class="table-responsive">
				<table class="table table-hover table-sm align-middle mb-0 small">
					<thead class="table-light text-uppercase text-muted" style="font-size:11px; letter-spacing:0.04em;">
						<tr>
							<th class="sort-th ps-3">ID <span class="sort-icon">↕</span></th>
							<th class="sort-th">From <span class="sort-icon">↕</span></th>
							<th class="sort-th">Party <span class="sort-icon">↕</span></th>
							<th class="sort-th">Status <span class="sort-icon">↕</span></th>
							<th class="sort-th">Type <span class="sort-icon">↕</span></th>
							<th class="sort-th">Stage <span class="sort-icon">↕</span></th>
							<th class="sort-th">Owner <span class="sort-icon">↕</span></th>
							<th class="sort-th">Date <span class="sort-icon">↕</span></th>
						</tr>
					</thead>
					<tbody>${rows}</tbody>
				</table>
			</div>
		`);

  
    $("#opp-table-container tbody tr").on("click", function () {
      frappe.set_route("Form", "Opportunity", $(this).data("name"));
    });

    // Column sort
    const col_keys = [
      "name",
      "opportunity_from",
      "party_name",
      "status",
      "opportunity_type",
      "opportunity_amount",
      "sales_stage",
      "_assign",
      "transaction_date",
    ];

    $("#opp-table-container thead th.sort-th").on("click", function () {
      let key = col_keys[$(this).index()];
      let asc = $(this).data("sort") !== "asc";
      $(this).data("sort", asc ? "asc" : "desc");

      let sorted = [...data].sort((a, b) => {
        let va = a[key] || "",
          vb = b[key] || "";
        return asc ? (va > vb ? 1 : -1) : va < vb ? 1 : -1;
      });

      $("#opp-table-container .sort-icon").text("↕");
      $(this)
        .find(".sort-icon")
        .text(asc ? "↑" : "↓");
      render_table(sorted);
    });
  }

  // -- Update Stats 
  function update_stats(data) {
    $("#stat-total").text(data.length);
    $("#stat-open").text(data.filter((d) => d.status === "Open").length);
    $("#stat-converted").text(
      data.filter((d) => d.status === "Converted").length,
    );

    
   
  }

  // -- Live Search
  $(page.body).on("input", "#opp-search", function () {
    let q = $(this).val().toLowerCase();
    let filtered = all_data.filter(
      (d) =>
        (d.name || "").toLowerCase().includes(q) ||
        (d.party_name || "").toLowerCase().includes(q) ||
        (d.opportunity_from || "").toLowerCase().includes(q) ||
        (d.status || "").toLowerCase().includes(q) ||
        (d.sales_stage || "").toLowerCase().includes(q),
    );
    render_table(filtered);
  });

  // -- Fetch Data
  function load_opportunities() {
    $("#opp-table-container").html(`
			<div class="text-center text-muted py-5">
				<div class="spinner-border spinner-border-sm me-2" role="status"></div>
				Loading opportunities...
			</div>
		`);

    let status_filter = page.fields_dict.status_filter.get_value();
    let filters = {};
    if (status_filter) filters["status"] = status_filter;

    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Opportunity",
        fields: [
          "name",
          "opportunity_from",
          "party_name",
          "status",
          "opportunity_type",
          "opportunity_amount",
          "sales_stage",
          "transaction_date",
          "_assign",
        ],
        filters: filters,
        limit: 500,
        order_by: "transaction_date desc",
      },
      callback: function (r) {
        if (r.exc) {
          $("#opp-table-container").html(`
						<div class="text-center text-danger py-5">
							<div style="font-size:2rem;">⚠️</div>
							<p class="mt-2 mb-0">Error loading data. Please try again.</p>
						</div>
					`);
          return;
        }

        all_data = r.message || [];
        update_stats(all_data);
        render_table(all_data);

        let q = $("#opp-search").val();
        if (q) $("#opp-search").trigger("input");
      },
    });
  }

  // Initial load
  load_opportunities();
};
