const formatPercent = (ratio) => `${(ratio * 100).toFixed(1)}%`;

const setStatus = (message, tone = "info") => {
	const statusElement = document.getElementById("status-message");
	if (!statusElement) {
		return;
	}

	statusElement.textContent = message;
	statusElement.className = `status-message ${tone}`;
};

const toResultsArray = (results) =>
	Object.entries(results).map(([name, data]) => ({ name, ...data }));

const renderSummaryTable = (results) => {
	const summaryBody = document.getElementById("summary-body");
	if (!summaryBody) {
		return;
	}

	const rows = toResultsArray(results);
	summaryBody.innerHTML = "";

	if (!rows.length) {
		summaryBody.innerHTML = `
			<tr class="placeholder-row">
				<td colspan="5">No data to display.</td>
			</tr>
		`;
		return;
	}

	rows.forEach((entry) => {
		const row = document.createElement("tr");
		row.innerHTML = `
			<td>${entry.algorithm}</td>
			<td>${entry.page_faults}</td>
			<td>${entry.page_hits}</td>
			<td>${formatPercent(entry.fault_ratio)}</td>
			<td>${formatPercent(entry.hit_ratio)}</td>
		`;
		summaryBody.appendChild(row);
	});
};

const renderFaultChart = (results) => {
	const chartContainer = document.getElementById("bar-chart");
	if (!chartContainer) {
		return;
	}

	const rows = toResultsArray(results);
	chartContainer.innerHTML = "";

	if (!rows.length) {
		return;
	}

	const maxFaults = Math.max(...rows.map((entry) => entry.page_faults), 1);

	rows.forEach((entry, index) => {
		const chartRow = document.createElement("article");
		chartRow.className = "chart-row";

		const width = (entry.page_faults / maxFaults) * 100;

		chartRow.innerHTML = `
			<span class="chart-label">${entry.algorithm}</span>
			<div class="chart-track">
				<div class="chart-bar bar-${index % 3}" style="width: ${width}%"></div>
			</div>
			<span class="chart-value">${entry.page_faults}</span>
		`;

		chartContainer.appendChild(chartRow);
	});
};

const buildFrameCells = (frames) =>
	frames
		.map((value) => {
			const className = value === null ? "frame-cell empty" : "frame-cell";
			return `<span class="${className}">${value === null ? "-" : value}</span>`;
		})
		.join("");

const renderAlgorithmDetails = (results) => {
	const detailsContainer = document.getElementById("algorithm-details");
	if (!detailsContainer) {
		return;
	}

	const rows = toResultsArray(results);
	detailsContainer.innerHTML = "";

	if (!rows.length) {
		detailsContainer.innerHTML = "<p class=\"muted\">No details available.</p>";
		return;
	}

	rows.forEach((entry) => {
		const wrapper = document.createElement("details");
		wrapper.className = "trace-block";
		wrapper.open = true;

		const tableRows = entry.steps
			.map((step) => {
				const badgeClass = step.status === "hit" ? "hit" : "fault";
				const replacedValue = step.replaced === null ? "-" : step.replaced;

				return `
					<tr>
						<td>${step.step}</td>
						<td>${step.page}</td>
						<td><span class="status-pill ${badgeClass}">${step.status.toUpperCase()}</span></td>
						<td>${replacedValue}</td>
						<td><div class="frame-strip">${buildFrameCells(step.frames)}</div></td>
					</tr>
				`;
			})
			.join("");

		wrapper.innerHTML = `
			<summary>
				<h3>${entry.algorithm}</h3>
				<span>${entry.page_faults} faults / ${entry.page_hits} hits</span>
			</summary>
			<div class="trace-table-wrap">
				<table class="trace-table">
					<thead>
						<tr>
							<th>Step</th>
							<th>Page</th>
							<th>Status</th>
							<th>Replaced</th>
							<th>Frames After Access</th>
						</tr>
					</thead>
					<tbody>
						${tableRows}
					</tbody>
				</table>
			</div>
		`;

		detailsContainer.appendChild(wrapper);
	});
};

const runSimulation = async ({ frames, pages, algorithm }) => {
	const response = await fetch("/api/simulate", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({
			frames,
			pages,
			algorithm,
		}),
	});

	const data = await response.json();

	if (!response.ok || !data.ok) {
		throw new Error(data.error || "Simulation failed. Please verify your inputs.");
	}

	return data;
};

const initializeSimulatorPage = () => {
	const form = document.getElementById("simulation-form");
	if (!form) {
		return;
	}

	const framesInput = document.getElementById("frames");
	const pagesInput = document.getElementById("pages");
	const algorithmInput = document.getElementById("algorithm");
	const sampleButton = document.getElementById("load-sample");

	if (sampleButton && framesInput && pagesInput && algorithmInput) {
		sampleButton.addEventListener("click", () => {
			framesInput.value = "3";
			pagesInput.value = "7 0 1 2 0 3 4 2 3 0 3 2";
			algorithmInput.value = "all";
			setStatus("Sample input loaded. Click Run Simulation.", "info");
		});
	}

	form.addEventListener("submit", async (event) => {
		event.preventDefault();

		if (!framesInput || !pagesInput || !algorithmInput) {
			return;
		}

		const payload = {
			frames: framesInput.value.trim(),
			pages: pagesInput.value.trim(),
			algorithm: algorithmInput.value,
		};

		if (!payload.frames || !payload.pages) {
			setStatus("Please provide both frame count and page reference string.", "error");
			return;
		}

		try {
			setStatus("Running simulation...", "loading");

			const response = await runSimulation(payload);
			renderSummaryTable(response.results);
			renderFaultChart(response.results);
			renderAlgorithmDetails(response.results);

			setStatus("Simulation completed successfully.", "success");
		} catch (error) {
			setStatus(error.message, "error");
		}
	});
};

document.addEventListener("DOMContentLoaded", () => {
	initializeSimulatorPage();
	initializeTeamManager();
});

const TEAM_STORAGE_KEY = "prs-team-members-v1";

const initializeTeamManager = () => {
	const teamForm = document.getElementById("team-form");
	const teamTableBody = document.getElementById("team-table-body");
	const defaultTeamScript = document.getElementById("default-team-members");
	const resetTeamButton = document.getElementById("reset-team");

	if (!teamForm || !teamTableBody || !defaultTeamScript) {
		return;
	}

	const nameInput = document.getElementById("team-name");
	const registrationInput = document.getElementById("team-registration");
	const rollInput = document.getElementById("team-roll");

	let defaultMembers = [];
	try {
		defaultMembers = JSON.parse(defaultTeamScript.textContent || "[]");
	} catch (error) {
		defaultMembers = [];
	}

	const loadStoredMembers = () => {
		try {
			const stored = localStorage.getItem(TEAM_STORAGE_KEY);
			if (!stored) {
				return null;
			}
			const parsed = JSON.parse(stored);
			return Array.isArray(parsed) ? parsed : null;
		} catch (error) {
			return null;
		}
	};

	let members = loadStoredMembers() || defaultMembers;

	const saveMembers = () => {
		try {
			localStorage.setItem(TEAM_STORAGE_KEY, JSON.stringify(members));
		} catch (error) {
			// Ignore storage failures; rendering still works in memory.
		}
	};

	const renderMembers = () => {
		teamTableBody.innerHTML = "";

		if (!members.length) {
			teamTableBody.innerHTML = `
				<tr class="placeholder-row">
					<td colspan="4">No members added yet. Use the form above to add a member.</td>
				</tr>
			`;
			return;
		}

		members.forEach((member, index) => {
			const row = document.createElement("tr");
			row.innerHTML = `
				<td>${member.name}</td>
				<td>${member.registration}</td>
				<td>${member.roll}</td>
				<td>
					<button class="btn btn-danger table-action" type="button" data-remove-index="${index}">
						Remove
					</button>
				</td>
			`;
			teamTableBody.appendChild(row);
		});
	};

	teamForm.addEventListener("submit", (event) => {
		event.preventDefault();

		const name = nameInput?.value.trim() || "";
		const registration = registrationInput?.value.trim() || "";
		const roll = rollInput?.value.trim() || "";

		if (!name || !registration || !roll) {
			return;
		}

		members.push({ name, registration, roll });
		saveMembers();
		renderMembers();
		teamForm.reset();
	});

	teamTableBody.addEventListener("click", (event) => {
		const target = event.target;
		if (!(target instanceof HTMLElement)) {
			return;
		}

		const removeIndex = target.getAttribute("data-remove-index");
		if (removeIndex === null) {
			return;
		}

		const index = Number(removeIndex);
		if (Number.isNaN(index) || index < 0 || index >= members.length) {
			return;
		}

		members.splice(index, 1);
		saveMembers();
		renderMembers();
	});

	if (resetTeamButton) {
		resetTeamButton.addEventListener("click", () => {
			members = [...defaultMembers];
			try {
				localStorage.removeItem(TEAM_STORAGE_KEY);
			} catch (error) {
				// Ignore storage failures; reset still works for this session.
			}
			renderMembers();
		});
	}

	renderMembers();
};
