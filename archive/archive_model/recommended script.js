document.addEventListener("DOMContentLoaded", function() {
    const userId = "geovanny"; // Replace "123" with the desired user ID
    const recommendationLimit = 100; // Specify the maximum number of recommendations to display

    fetch("/app/data/listening_history.csv") // Replace with the actual path to the CSV file inside docker
        .then(response => response.text())
        .then(data => {
            const rows = data.split("\n");
            const table = document.getElementById("historyTable");

            // Create table header
            const headerRow = document.createElement("tr");
            const headers = rows[0].split(",");
            headers.forEach((header, index) => {
                if (index !== 0) {
                    const th = document.createElement("th");
                    th.textContent = header;
                    headerRow.appendChild(th);
                }
            });
            table.appendChild(headerRow);

            // Sort rows by date in descending order
            const sortedRows = rows.slice(1).sort((a, b) => {
                const dateA = new Date(a.split(",")[0]); // Assuming the date is in the first column
                const dateB = new Date(b.split(",")[0]);
                return dateB - dateA;
            });

            // Create table rows based on user ID and recommendation limit
            let count = 0;
            for (let i = 0; i < sortedRows.length; i++) {
                if (count >= recommendationLimit) {
                    break;
                }

                const rowData = sortedRows[i].split(",");
                const rowUserId = rowData[0]; // Assuming the user ID is in the first column (index 0)

                if (rowUserId.trim() === userId.trim()) {
                    const row = document.createElement("tr");

                    rowData.forEach((cellData, index) => {
                        if (index !== 0) {
                            const td = document.createElement("td");
                            td.textContent = cellData.trim();
                            row.appendChild(td);
                        }
                    });

                    table.appendChild(row);
                    count++;
                }
            }
        })
        .catch(error => console.error(error));
});