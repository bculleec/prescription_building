min_raster_value = 0
max_raster_value = 0
raster_array = []

raster_file = null

function updateValues(sourceTable, targetTable) {
    const sourceRows = sourceTable.querySelectorAll('tbody tr');
    const targetRows = targetTable.querySelectorAll('tbody tr');

    

    min_value = 9999
    max_value = -9999
    total_acres = 0
    total_product = 0

    sourceRows.forEach((row, index) => {
        const value = parseFloat(row.cells[5].innerText);
        const zone_area = parseFloat(row.cells[4].innerText)
        const zone_product = value * zone_area

        if (value < min_value) {
            min_value = value
        }

        if (value > max_value) {
            max_value = value
        }

        total_acres += zone_area
        total_product += zone_product

        if (!isNaN(value)) {
            targetRows[index].cells[1].innerText = (value * 2).toFixed(2); 
        }
    });

    const avg_rate = total_product / total_acres

    targetRows[0].cells[1].innerText = avg_rate.toFixed(2);
    targetRows[1].cells[1].innerText = (total_product / 2.20462).toFixed(2);
    targetRows[2].cells[1].innerText = min_value.toFixed(2);
    targetRows[3].cells[1].innerText = max_value.toFixed(2);
    targetRows[4].cells[1].innerText = total_acres.toFixed(2);
    
}

function Nodata(value, nodata) {
    if (value === nodata)
        return false
    return true 
}

function syncMinMax(sourceTable, targetTable) {
    const sourceRows = sourceTable.querySelectorAll('tbody tr');
    const targetRows = targetTable.querySelectorAll('tbody tr');

    const avg_rate = parseFloat(targetRows[0].cells[1].innerText);
    const total_product = parseFloat(targetRows[1].cells[1].innerText) * 2.20462;
    new_min_rate = parseFloat(targetRows[2].cells[1].innerText);
    new_max_rate = parseFloat(targetRows[3].cells[1].innerText);
    const total_acres = parseFloat(targetRows[4].cells[1].innerText);

    if ( (total_product < ((avg_rate * total_acres) - 0.1)) || (total_product > ((avg_rate * total_acres) + 0.1))) {
        // Then the avg rate or the total product has been changed
        // Check if total product has been changed
        
        test_total_product = 0

        sourceRows.forEach((row, index) => {

        
            const minCell = row.cells[5]; 
            const value = parseFloat(minCell.innerText);
    
            console.log(value)
            test_total_product += value * parseFloat(row.cells[4].innerText)


        })
        
        if ((test_total_product < total_product - 0.1) ||(test_total_product > total_product + 0.1)){
            console.log("Total product has been changed")

            // Change the average product
            new_avg_rate = total_product / total_acres
            targetTable.querySelectorAll('tbody tr')[0].cells[1].innerText = new_avg_rate.toFixed(2)
            // Other changes to min and max will follow from this

            change_ratio = new_avg_rate / avg_rate

        } else {
            console.log("Average product has been changed")
            
            // Update all values in the zone table and call updateValues to reflect changes in second table
            
            change_ratio = avg_rate / (total_product / total_acres)
            // window.alert(change_ratio)
        }

        cur_row  = 0
        sourceRows.forEach((row, index) => {

            
            const minCell = row.cells[5]; 
            const value = parseFloat(minCell.innerText);

            console.log(value)

            // window.alert(value + " x " + change_ratio)

            new_value = value * change_ratio
            if (new_value < new_min_rate) {    
                targetTable.querySelectorAll('tbody tr')[2].cells[1].innerText = new_value.toFixed(2)
                new_min_rate = new_value
            }
            if (new_value > new_max_rate) {
                targetTable.querySelectorAll('tbody tr')[3].cells[1].innerText = new_value.toFixed(2)
                new_max_rate = new_value
            }
            
            sourceTable.querySelectorAll('tbody tr')[cur_row].cells[5].innerText = new_value.toFixed(2)
            cur_row+=1;
        })

        // Reflect changes in second table
        updateValues(sourceTable, targetTable)
            
    }

    

    // window.alert(new_min_rate)
    cur_row  = 0
    sourceRows.forEach((row, index) => {

        
        const minCell = row.cells[5]; 
        const value = parseFloat(minCell.innerText);

        console.log(value)

        if (value < new_min_rate) {
            sourceTable.querySelectorAll('tbody tr')[cur_row].cells[5].innerText = new_min_rate.toFixed(2)
            updateValues(sourceTable, targetTable)
        }

        if (value > new_max_rate) {
            sourceTable.querySelectorAll('tbody tr')[cur_row].cells[5].innerText = new_max_rate.toFixed(2)
            updateValues(sourceTable, targetTable)
        }

        cur_row += 1;
    });
}

document.querySelectorAll('td[contenteditable="true"]').forEach(cell => {
    cell.addEventListener('blur', (event) => {
        const sourceTable = event.target.closest('table');
        const targetTable = sourceTable.id === 'table1' ? document.getElementById('table2') : document.getElementById('table1');
        updateValues(sourceTable, targetTable);
    });
});

document.querySelectorAll('#table2 td[contenteditable="true"]').forEach(cell => {
    cell.addEventListener('blur', (event) => {
        const targetTable = event.target.closest('table');
        const sourceTable = targetTable.id === 'table1' ? document.getElementById('table2') : document.getElementById('table1');
        syncMinMax(sourceTable, targetTable);
    });
});

// Handling the .tiff file upload

const { fromUrl, fromUrls, fromArrayBuffer, fromBlob } = GeoTIFF;
document.getElementById('uploadButton').addEventListener('click', () => {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a TIFF file.");
        return;
    }

    if (!file.name.endsWith('.tif') && !file.name.endsWith('.tiff')) {
        alert("Please upload a valid TIFF file.");
        return;
    }

    const reader = new FileReader();
    reader.onload = async (event) => {
        // This is where you can handle the uploaded TIFF data
        const arrayBuffer = event.target.result;
        console.log("Uploaded TIFF file data:", arrayBuffer);
        document.getElementById('uploadStatus').innerText = "Upload successful!";
        
        // Here you could integrate with a library to process the TIFF if needed
        // For example: parseTIFF(arrayBuffer) or similar function

        
        const tiff = await fromArrayBuffer(arrayBuffer);
        const image = await tiff.getImage();

        const width = image.getWidth();
        const height = image.getHeight();
        const tileWidth = image.getTileWidth();
        const tileHeight = image.getTileHeight();
        const samplesPerPixel = image.getSamplesPerPixel();

        // Send file to flask

        const blob = new Blob([arrayBuffer], { type: 'image/tiff' });

        const formData = new FormData();
        formData.set('file', blob, 'file'); 

        raster_file = formData

        const response = await fetch("/post_raster_data/4", {
            method: "POST",
            body: formData
        });

        const responseData = await response.json(); 
        console.log(responseData);

        // Build the initial table here
        var table = document.getElementById("table1");
        table.innerHTML = `<thead>
            <tr>
                <th>Zone ID</th>
                <th>Min Value in Zone</th>
                <th>Max Value in Zone</th>
                <th>Average value in zone</th>
                <th>Total Acres</th>
                <th>Lbs/Ac Product in Script</th>
            </tr>
        </thead>`;

        let body = table.createTBody()

        for (let i = 0; i < 4; i++) {
            
            var row = body.insertRow(-1);
            var id_cell = row.insertCell(0);
            var min_cell = row.insertCell(1);
            var max_cell = row.insertCell(2);
            var mean_cell = row.insertCell(3);
            var acres_cell = row.insertCell(4);
            var zone_rate = row.insertCell(5);

            id_cell.innerText = responseData['Zone ID'][i]
            division_low_bound = responseData['Min Value in zone'][i]
            division_high_bound = responseData['Max Value in zone'][i]
            min_cell.innerText = (division_low_bound).toFixed(2)
            if (i ===0 )
                min_cell.innerText = (parseFloat(division_low_bound) - 0.01).toFixed(2)
            max_cell.innerText = (division_high_bound).toFixed(2)
            if (i ===3) // Eventually change to the last value in the number of subdivisions (numSubdivisions - 1)
                max_cell.innerText = (parseFloat(division_high_bound) + 0.01).toFixed(2)
            zone_rate.contentEditable = true;
            // zone_rate.bgColor = "#001100" // Can change to a good color for signaling editable field here
            // Find the average value per zone
            
            
            
            mean_cell.innerText = (responseData['Average value in zone'][i]).toFixed(2)

            // Make call to python server to get the area here
            acres_cell.innerText = responseData['Total Acres'][i].toFixed(2)

            zone_rate.innerText = 1

            // May need to reattach the editable listeners
            document.querySelectorAll('td[contenteditable="true"]').forEach(cell => {
                cell.addEventListener('blur', (event) => {
                    const sourceTable = event.target.closest('table');
                    const targetTable = sourceTable.id === 'table1' ? document.getElementById('table2') : document.getElementById('table1');
                    updateValues(sourceTable, targetTable);
                });
            });
        }

        // when we are actually dealing with geo-data the following methods return
        // meaningful results:
        const origin = image.getOrigin();
        const resolution = image.getResolution();
        const bbox = image.getBoundingBox();
        const data = image.readRasters().then((result) => {
            console.log(result[0])
            console.log(Math.min(...result[0].filter(Nodata(-32768))))
            console.log(Math.max(...result[0]))

            min_raster_value = Math.min(...result[0].filter(Nodata(32768)))
            max_raster_value = Math.max(...result[0])
            raster_array = result[0]
            // We can use these results to build the initial table

            // Send the file over to python
            // fetch("/post_raster_data", {
            //     method: "POST",
            //     body: JSON.stringify({
            //       userId: 1,
            //       title: "Fix my bugs",
            //       completed: false,
            //       raster_data: Array.from(file)
            //     }),
            //     headers: {
            //       "Content-type": "application/json; charset=UTF-8"
            //     }
            //   });
        });
        

    };

    reader.onerror = (error) => {
        console.error("Error reading file:", error);
        document.getElementById('uploadStatus').innerText = "Error uploading file.";
    };

    reader.readAsArrayBuffer(file); // Read the file as an ArrayBuffer
    
});

document.getElementById('exportButton').addEventListener('click', () => {
    // Send POST request to python for processing the shapefile & send to user

    // Grab all values from table
    sourceRows = document.querySelectorAll('#table1 tbody tr');
    
    
    zones = []
    zone = {}
    let filename = document.getElementById("exportFilename").value

    sourceRows.forEach((row, index) => {
        const zone_id = parseFloat(row.cells[0].innerText)
        const min_val = parseFloat(row.cells[1].innerText)
        const max_val = parseFloat(row.cells[2].innerText)
        const avg_val = parseFloat(row.cells[3].innerText)
        const total_acres = parseFloat(row.cells[4].innerText)
        const value = parseFloat(row.cells[5].innerText);
        
        zone = {
            "Zone ID":zone_id,
            "Min Val":min_val,
            "Max Val":max_val,
            "Avg Val":avg_val,
            "Total Acres":total_acres,
            "Value":value,
            "Filename":filename
        }
        zones.push(zone)
        
    })
    console.log(zones)

    // Append to the formData() raster_file & send over
    const blob = new Blob([JSON.stringify(zones)], { type: 'application/json' });

    // raster_file.append('file2', blob, 'file2'); 

    sending_file = raster_file
    sending_file.set('file2', blob, 'file2'); 


    const response = fetch("/export_prescription/4", {
        method: "POST",
        body: sending_file
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.blob(); 
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename + '_prescription.zip';
        document.body.appendChild(a); 
        a.click(); 
        a.remove(); 
        window.URL.revokeObjectURL(url); 
    })
    .catch(error => {
        console.error('There was a problem with the fetch operation:', error);
    });

});

// document.getElementById('buildTablesButton').addEventListener('click', () => {
//     num_divisions = parseInt(document.getElementById('numSubdivisions').value)
//     // window.alert(min_raster_value + "-" + max_raster_value + " with " + num_divisions + " subdivisions")

//     // Add Rows to the table for each subdivision
//     var table = document.getElementById("table1");
//     table.innerHTML = `<thead>
//         <tr>
//             <th>Zone ID</th>
//             <th>Min Value in Zone</th>
//             <th>Max Value in Zone</th>
//             <th>Average value in zone</th>
//             <th>Total Acres</th>
//             <th>Lbs/Ac Product in Script</th>
//         </tr>
//     </thead>`;

//     let body = table.createTBody()

//     for (let i = 0; i < num_divisions; i++) {
        
//         var row = body.insertRow(-1);
//         var cell1 = row.insertCell(0);
//         var min_cell = row.insertCell(1);
//         var max_cell = row.insertCell(2);
//         var mean_cell = row.insertCell(3);
//         var acres_cell = row.insertCell(4);
//         var zone_rate = row.insertCell(5);

//         cell1.innerText = i + 1
//         division_low_bound = (i * ((max_raster_value - min_raster_value) / num_divisions)) + min_raster_value
//         division_high_bound = division_low_bound + ((max_raster_value - min_raster_value) / num_divisions)
//         min_cell.innerText = (division_low_bound).toFixed(2)
//         max_cell.innerText = (division_high_bound).toFixed(2)
//         zone_rate.contentEditable = true;

//         // Find the average value per zone
        
//         zone_values = filterRange(raster_array, division_low_bound, division_high_bound)

//         console.log(zone_values)
//         sum = 0
//         indexes = 0
//         for (val in zone_values) {
//             sum += parseFloat(zone_values[val])
//             indexes += 1
//         }
//         console.log(sum)
        
//         mean_cell.innerText = (sum / indexes).toFixed(2)

//         // Make call to python server to get the area here
//         acres_cell.innerText = 10

//         zone_rate.innerText = 1

//         // May need to reattach the editable listeners
//         document.querySelectorAll('td[contenteditable="true"]').forEach(cell => {
//             cell.addEventListener('blur', (event) => {
//                 const sourceTable = event.target.closest('table');
//                 const targetTable = sourceTable.id === 'table1' ? document.getElementById('table2') : document.getElementById('table1');
//                 updateValues(sourceTable, targetTable);
//             });
//         });
//     }

// });


function filterRange(arr, a, b) {
    // added brackets around the expression for better readability
    return arr.filter(item => (a <= item && item <= b));
  }