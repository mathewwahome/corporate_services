/* ============================================================
 * SECTION 1 - NUMBER CARDS
 * ============================================================ */
frappe.provide('JobDashboard.NumberCards');

JobDashboard.NumberCards = {

	cards: [
		{ name: 'Job Openings',            color: '#2490ef', icon: 'fa fa-briefcase'    },
		{ name: 'Accepted Job Applicants', color: '#28a745', icon: 'fa fa-check-circle' },
		{ name: 'Rejected Job Applicants', color: '#dc3545', icon: 'fa fa-times-circle' },
	],

	load: function() {
		const $row = $('#number-cards-row').empty();
		this.cards.forEach(cfg => {
			$row.append(this._skeleton(cfg));
			this._fetch_doc(cfg);
		});
	},

	_safe_id: function(name) {
		return 'nc-' + name.toLowerCase().replace(/[^a-z0-9]/g, '-');
	},

	_skeleton: function(cfg) {
		const id = this._safe_id(cfg.name);
		return `
			<div class="col-12 col-sm-6 col-lg-4 mb-3 jod-number-card"
			     data-card="${frappe.utils.escape_html(cfg.name)}">
				<div class="card h-100">
					<div class="card-body">
						<div class="card-label mb-2">
							<i class="${cfg.icon} mr-1"></i>
							${frappe.utils.escape_html(cfg.name)}
						</div>
						<div class="card-value" id="${id}">
							<div class="spinner-border spinner-border-sm text-muted" role="status"></div>
						</div>
					</div>
					<div style="height:3px;background:${cfg.color};border-radius:0 0 8px 8px;"></div>
				</div>
			</div>`;
	},

	_set_value: function(name, value) {
		$('#' + this._safe_id(name)).text(value);
	},

	_set_error: function(name, msg) {
		$('#' + this._safe_id(name)).html('<small class="text-danger">' + msg + '</small>');
	},

	_fetch_doc: function(cfg) {
		const self = this;
		frappe.call({
			method: 'frappe.client.get',
			args: { doctype: 'Number Card', name: cfg.name },
			callback: function(r) {
				if (!r.message) { self._set_error(cfg.name, 'Card not found'); return; }
				self._fetch_value(r.message);
			},
			error: function() { self._set_error(cfg.name, 'Failed to load'); }
		});
	},

	_fetch_value: function(doc) {
		const self = this;
		frappe.call({
			method: 'frappe.desk.doctype.number_card.number_card.get_result',
			args: {
				doc     : doc,
				filters : doc.filters_json || '[]',
				to_date : frappe.datetime.get_today()
			},
			callback: function(res) {
				const val = (res.message !== undefined && res.message !== null)
					? Number(res.message).toLocaleString()
					: '-';
				self._set_value(doc.name, val);
			},
			error: function() { self._set_error(doc.name, 'Error'); }
		});
	},

	bind_events: function() {
		$(document).on('click', '.jod-number-card', function() {
			const card_name = $(this).data('card');
			if (!card_name) return;
			frappe.call({
				method: 'frappe.client.get',
				args: { doctype: 'Number Card', name: card_name },
				callback: function(r) {
					if (!r.message || !r.message.document_type) return;
					let filters = [];
					try { filters = JSON.parse(r.message.filters_json || '[]'); } catch(e) {}
					frappe.set_route('List', r.message.document_type, { filters: filters });
				}
			});
		});
	}
};




/* ============================================================
 * SECTION 2 - CHART
 * ============================================================ */
frappe.provide('JobDashboard.Chart');

JobDashboard.Chart = {

	CHART_NAME: 'Job Applications By Opening',

	load: function() {
		const self = this;
		const $container = $('#jod-chart-container');
		$container.html(
			'<div class="text-center text-muted py-4">'
			+ '<div class="spinner-border spinner-border-sm mr-2" role="status"></div>'
			+ 'Loading chart…</div>'
		);

		frappe.call({
			method: 'frappe.client.get',
			args: { doctype: 'Dashboard Chart', name: self.CHART_NAME },
			callback: function(r) {
				if (!r.message) {
					$container.html(
						'<div class="alert alert-warning m-3">Chart "'
						+ frappe.utils.escape_html(self.CHART_NAME) + '" not found.</div>'
					);
					return;
				}
				self._render(r.message);
			},
			error: function() {
				$container.html(
					'<div class="alert alert-danger m-3">Failed to load chart.</div>'
				);
			}
		});
	},

	_render: function(chart_doc) {
		const self    = this;
		const $container = $('#jod-chart-container');

		frappe.call({
			method: 'frappe.desk.doctype.dashboard_chart.dashboard_chart.get',
			args: {
				chart_name : chart_doc.name,
				filters    : chart_doc.filters_json || '[]',
				refresh    : 1
			},
			callback: function(r) {
				if (!r.message || !r.message.labels) {
					$container.html(
						'<div class="text-center text-muted py-4">No data available.</div>'
					);
					return;
				}

				const data     = r.message;
				const labels   = data.labels   || [];
				const datasets = data.datasets || [];

				if (!labels.length) {
					$container.html(
						'<div class="text-center text-muted py-4">No data available.</div>'
					);
					return;
				}

				$container.empty();

				try {
					new frappe.Chart('#jod-chart-container', {
						title     : '',
						data      : {
							labels   : labels,
							datasets : datasets
						},
						type      : chart_doc.type ? chart_doc.type.toLowerCase() : 'bar',
						height    : 280,
						colors    : ['#2490ef','#28a745','#dc3545','#f39c12'],
						axisOptions: { xIsSeries: 0 },
						tooltipOptions: {}
					});
				} catch(e) {
					self._render_fallback($container, labels, datasets);
				}
			},
			error: function() {
				$container.html(
					'<div class="alert alert-danger m-3">Failed to fetch chart data.</div>'
				);
			}
		});
	},

	_render_fallback: function($container, labels, datasets) {
		const values  = (datasets[0] && datasets[0].values) ? datasets[0].values : [];
		const max     = Math.max.apply(null, values) || 1;

		let html = '<div class="p-3">';
		labels.forEach(function(label, i) {
			const val = values[i] || 0;
			const pct = Math.round((val / max) * 100);
			html += '<div class="mb-2">'
				+ '<div class="d-flex justify-content-between mb-1">'
				+   '<small class="text-truncate" style="max-width:60%;">'
				+     frappe.utils.escape_html(label)
				+   '</small>'
				+   '<small class="font-weight-bold">' + val + '</small>'
				+ '</div>'
				+ '<div class="progress" style="height:8px;">'
				+   '<div class="progress-bar bg-primary" style="width:' + pct + '%"></div>'
				+ '</div>'
				+ '</div>';
		});
		html += '</div>';
		$container.html(html);
	}
};


/* ============================================================
 * SECTION 3 - JOB TABLE
 * ============================================================ */
frappe.provide('JobDashboard.JobTable');

JobDashboard.JobTable = {

	all_jobs     : [],
	app_counts   : {},
	sort_col     : 'posted_on',
	sort_order   : 'desc',
	search_fields: ['job_title','department','designation','employment_type',
	                'status','company','location','custom_work_mode'],

	_safe_id: function(name) {
		return 'app-count-' + name.replace(/[^a-zA-Z0-9]/g, '_');
	},

	load: function() {
		$('#job-loading').show();
		$('#job-table-wrapper').hide();
		$('#job-empty').hide();
		$('#job-count-info').text('');

		const self = this;
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Job Opening',
				fields: [
					'name', 'job_title', 'department', 'designation',
					'employment_type', 'status', 'posted_on',
					'company', 'location', 'closes_on',
					'custom_work_mode', 'custom_staff_requisition', 'vacancies'
				],
				limit_page_length: 500,
				order_by: 'posted_on desc'
			},
			callback: function(r) {
				$('#job-loading').hide();
				self.all_jobs = r.message || [];
				if (!self.all_jobs.length) { $('#job-empty').show(); return; }
				self._fetch_app_counts(self.all_jobs);
			},
			error: function(err) {
				$('#job-loading').html(
					'<div class="alert alert-danger m-3">Failed to load job openings.</div>'
				);
				console.error('Job Opening fetch error:', err);
			}
		});
	},

	_fetch_app_counts: function(jobs) {
		const self = this;
		self.app_counts = {};
		jobs.forEach(function(j) { self.app_counts[j.name] = null; });
		self._render(jobs);

		jobs.forEach(function(job) {
			frappe.call({
				method: 'frappe.client.get_count',
				args: {
					doctype : 'Job Applicant',
					filters : [['Job Applicant', 'job_title', '=', job.name]]
				},
				callback: function(r) {
					const count     = (r.message !== undefined && r.message !== null)
					                  ? parseInt(r.message, 10) : 0;
					self.app_counts[job.name] = count;
					const badge_cls = count > 0 ? 'badge-primary' : 'badge-secondary';
					const safe_id   = self._safe_id(job.name);
					$('#' + safe_id).replaceWith(
						'<span class="badge ' + badge_cls + '" id="' + safe_id + '">'
						+ count + '</span>'
					);
				},
				error: function() {
					const safe_id = self._safe_id(job.name);
					$('#' + safe_id).replaceWith(
						'<span class="badge badge-secondary" id="' + safe_id + '">0</span>'
					);
				}
			});
		});
	},

	_render: function(jobs) {
		const $tbody = $('#job-table-body').empty();

		if (!jobs.length) {
			$('#job-table-wrapper').hide();
			$('#job-empty').show();
			$('#job-count-info').text('');
			return;
		}

		$('#job-empty').hide();
		$('#job-table-wrapper').show();

		const self = this;
		jobs.forEach(function(job, idx) {
			const status_badge = JobDashboard.JobTable._status_badge(job.status);
			const mode_badge   = JobDashboard.JobTable._mode_badge(job.custom_work_mode);
			const posted       = job.posted_on
				? frappe.datetime.str_to_user(job.posted_on) : '-';
			const closes       = job.closes_on
				? frappe.datetime.str_to_user(job.closes_on) : '-';
			const count        = self.app_counts[job.name];
			const safe_id      = self._safe_id(job.name);

			const app_cell = (count === null)
				? '<div class="spinner-border spinner-border-sm text-muted" id="'
				  + safe_id + '" role="status"></div>'
				: '<span class="badge ' + (count > 0 ? 'badge-primary' : 'badge-secondary')
				  + '" id="' + safe_id + '">' + count + '</span>';

			$tbody.append(
				'<tr data-name="'  + frappe.utils.escape_html(job.name) + '"'
				+ '  data-title="' + frappe.utils.escape_html(job.job_title || '') + '">'

				// Row number
				+ '<td class="text-center text-muted small">' + (idx + 1) + '</td>'

				// Job Title
				+ '<td>'
				+   '<a href="/app/job-opening/' + encodeURIComponent(job.name)
				+   '" class="text-primary font-weight-medium">'
				+     frappe.utils.escape_html(job.job_title || '-')
				+   '</a>'
				+   (job.custom_staff_requisition
					? '<br><small class="text-muted">Req: '
					  + frappe.utils.escape_html(job.custom_staff_requisition) + '</small>'
					: '')
				+ '</td>'

				// Department
				+ '<td>' + frappe.utils.escape_html(job.department || '-') + '</td>'

				// Designation
				+ '<td>' + frappe.utils.escape_html(job.designation || '-') + '</td>'

				// Company / Location
				+ '<td>'
				+   '<div>' + frappe.utils.escape_html(job.company || '-') + '</div>'
				+   '<small class="text-muted">'
				+     '<i class="fa fa-map-marker mr-1"></i>'
				+     frappe.utils.escape_html(job.location || '-')
				+   '</small>'
				+ '</td>'

				// Employment Type + Work Mode
				+ '<td>'
				+   '<div>' + frappe.utils.escape_html(job.employment_type || '-') + '</div>'
				+   (job.custom_work_mode ? '<div>' + mode_badge + '</div>' : '')
				+ '</td>'

				// Vacancies
				+ '<td class="text-center">'
				+   (job.vacancies
					? '<span class="badge badge-info">' + job.vacancies + '</span>'
					: '<span class="text-muted">-</span>')
				+ '</td>'

				// Status
				+ '<td><span class="badge ' + status_badge + '">'
				+   frappe.utils.escape_html(job.status || '-') + '</span>'
				+ '</td>'

				// Posted On / Closes On
				+ '<td>'
				+   '<div><small class="text-muted">Posted:</small> ' + posted + '</div>'
				+   '<div><small class="text-muted">Closes:</small> ' + closes + '</div>'
				+ '</td>'

				// Applications
				+ '<td class="text-center">'
				+   '<button class="btn btn-sm btn-outline-primary jod-app-link"'
				+   '  data-job="'   + frappe.utils.escape_html(job.name)      + '"'
				+   '  data-title="' + frappe.utils.escape_html(job.job_title || '') + '">'
				+   app_cell
				+   ' <span>View</span>'
				+   '</button>'
				+ '</td>'

				+ '</tr>'
			);
		});

		$('#job-count-info').text(
			'Showing ' + jobs.length + ' of ' + this.all_jobs.length
			+ ' record' + (this.all_jobs.length !== 1 ? 's' : '')
		);
	},

	_status_badge: function(status) {
		if (!status) return 'badge-secondary';
		switch (status.toLowerCase()) {
			case 'open':    return 'badge-success';
			case 'closed':  return 'badge-danger';
			case 'on hold': return 'badge-warning';
			default:        return 'badge-secondary';
		}
	},

	_mode_badge: function(mode) {
		if (!mode) return '';
		const cls = {
			'remote'  : 'badge-info',
			'onsite'  : 'badge-secondary',
			'on-site' : 'badge-secondary',
			'hybrid'  : 'badge-warning'
		}[mode.toLowerCase()] || 'badge-secondary';
		return '<span class="badge ' + cls + '">' + frappe.utils.escape_html(mode) + '</span>';
	},

	_matches: function(job, q) {
		return this.search_fields.some(function(k) {
			return (job[k] || '').toLowerCase().includes(q);
		});
	},

	bind_events: function() {
		const self = this;

		$(document).on('input', '#job-search', function() {
			const q = $(this).val().toLowerCase().trim();
			self._render(q ? self.all_jobs.filter(function(j) {
				return self._matches(j, q);
			}) : self.all_jobs);
		});

		$(document).on('click', '#job-table thead th.sortable', function() {
			const col = $(this).data('col');
			if (!col) return;
			self.sort_order = (self.sort_col === col && self.sort_order === 'asc') ? 'desc' : 'asc';
			self.sort_col   = col;
			$('#job-table thead th').removeClass('sort-asc sort-desc');
			$(this).addClass('sort-' + self.sort_order);
			self.all_jobs.sort(function(a, b) {
				const vA = (a[col] || '').toString().toLowerCase();
				const vB = (b[col] || '').toString().toLowerCase();
				return self.sort_order === 'asc'
					? (vA < vB ? -1 : vA > vB ? 1 : 0)
					: (vA > vB ? -1 : vA < vB ? 1 : 0);
			});
			const q = $('#job-search').val().toLowerCase().trim();
			self._render(q ? self.all_jobs.filter(function(j) {
				return self._matches(j, q);
			}) : self.all_jobs);
		});

		$(document).on('click', '.jod-app-link', function(e) {
			e.stopPropagation();
			const job_opening = $(this).data('job');
			const job_title   = $(this).data('title');
			frappe.route_options = { job_opening: job_opening, job_title: job_title };
			frappe.set_route('job-applications');
		});

		$(document).on('click', '#job-table tbody tr', function(e) {
			if ($(e.target).closest('a').length) return;
			if ($(e.target).closest('.jod-app-link').length) return;
			frappe.set_route('Form', 'Job Opening', $(this).data('name'));
		});
	}
};


/* ============================================================
 * SECTION 4 - PAGE ENTRY POINT
 * ============================================================ */
frappe.pages['job-opening-dashboard'].on_page_load = function(wrapper) {

	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Job Opening Dashboard',
		single_column: true
	});

	page.add_button(__('Refresh'), function() {
		JobDashboard.NumberCards.load();
		JobDashboard.Chart.load();
		JobDashboard.JobTable.load();
	}, { icon: 'refresh' });

	frappe.dom.set_style(`
		.jod-number-card .card         { border-radius: 8px; transition: box-shadow .15s; }
		.jod-number-card .card:hover   { box-shadow: 0 2px 12px rgba(0,0,0,.12); cursor: pointer; }
		.jod-number-card .card-value   { font-size: 2rem; font-weight: 700; line-height: 1.1; }
		.jod-number-card .card-label   { font-size: .75rem; text-transform: uppercase;
		                                 letter-spacing: .05em; color: #8d99a6; }
		#job-table thead th.sortable        { cursor: pointer; white-space: nowrap; }
		#job-table thead th.sort-asc::after  { content: ' ↑'; opacity: .5; }
		#job-table thead th.sort-desc::after { content: ' ↓'; opacity: .5; }
		#job-table tbody tr                  { cursor: pointer; }
		.jod-app-link                        { white-space: nowrap; }
		.jod-app-link .badge                 { font-size: .8rem; padding: .3em .5em; }
		.jod-app-link span                   { font-size: .75rem; vertical-align: middle; }
		#job-table td                        { vertical-align: middle; }
	`);

	$(page.main).html(`
		<div class="container-fluid p-4">

			<div class="row mb-4" id="number-cards-row"></div>

			<!-- Chart -->
			<div class="row mb-4">
				<div class="col-12">
					<div class="card">
						<div class="card-header d-flex justify-content-between align-items-center py-2">
							<span class="font-weight-bold" style="font-size:.8rem;">
								<i class="fa fa-bar-chart mr-1 text-muted"></i>
								Job Applications By Opening
							</span>
							<button class="btn btn-sm btn-light" id="jod-chart-refresh">
								<i class="fa fa-refresh"></i>
							</button>
						</div>
						<div class="card-body p-0" id="jod-chart-container" style="min-height:100px;"></div>
					</div>
				</div>
			</div>

			<div class="d-flex justify-content-between align-items-center mb-2">
				<span class="text-muted font-weight-bold"
				      style="font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;">
					All Job Openings
				</span>
				<input id="job-search" type="text"
					class="form-control form-control-sm w-25"
					placeholder="Search by title, dept, location…" />
			</div>

			<div class="card">
				<div class="card-body p-0">
					<div id="job-loading" class="text-center text-muted py-5">
						<div class="spinner-border spinner-border-sm mr-2" role="status"></div>
						Loading job openings…
					</div>
					<div id="job-table-wrapper" style="display:none;">
						<table class="table table-hover mb-0" id="job-table">
							<thead class="thead-light">
								<tr>
									<th class="text-center" style="width:40px;">#</th>
									<th class="sortable" data-col="job_title">Job Title</th>
									<th class="sortable" data-col="department">Department</th>
									<th class="sortable" data-col="designation">Designation</th>
									<th class="sortable" data-col="company">Company / Location</th>
									<th class="sortable" data-col="employment_type">Type / Mode</th>
									<th class="sortable text-center" data-col="vacancies">Vacancies</th>
									<th class="sortable" data-col="status">Status</th>
									<th class="sortable" data-col="posted_on">Dates</th>
									<th class="text-center">Applications</th>
								</tr>
							</thead>
							<tbody id="job-table-body"></tbody>
						</table>
					</div>
					<div id="job-empty" class="text-center text-muted py-5" style="display:none;">
						<i class="fa fa-folder-open fa-2x d-block mb-2"></i>
						No job openings found.
					</div>
				</div>
			</div>
			<p class="text-muted small mt-2" id="job-count-info"></p>

		</div>
	`);

	JobDashboard.NumberCards.bind_events();
	JobDashboard.JobTable.bind_events();

	$(document).on('click', '#jod-chart-refresh', function() {
		JobDashboard.Chart.load();
	});

	JobDashboard.NumberCards.load();
	JobDashboard.Chart.load();
	JobDashboard.JobTable.load();
};