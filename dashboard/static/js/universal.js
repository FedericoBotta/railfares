/* d3.select("#selected-dropdown").text("");

d3.select('#jts-button')
    .on("click", function(){
    var selected = d3.select("#d3-dropdown").node().value;
    console.log( selected );
    d3.select("#selected-dropdown").text(selected);
    
    jQuery.ajax({
                url: '/GetJTSData',
                data: {'jts': selected},
                type: 'POST',
            });
    console.log(vartest);
    d3.select('#vartest').text(vartest);
    });
    
    
/* var map = L.map('map').fitWorld();
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map); */ 