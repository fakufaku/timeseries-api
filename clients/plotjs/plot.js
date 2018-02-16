$.getJSON( "https://data.robinscheibler.org/api/series/21", function( data ) {

  var lines = {};

  // Run through each sample of the time series
  $.each( data, function( key, val ) {
    // each sample can have a few values
    $.each( val['fields'], function(pkey, pval) {

      // If this is a new type of line, add it
      if (!(pkey in lines)) {
        lines[pkey] = {
          x: [],
          y: [],
          type: 'scatter',
          name: pkey
        };
      }

      // add the data
      lines[pkey]['x'].push(val['timestamp']);
      lines[pkey]['y'].push(pval);

    });
  });

  Plotly.newPlot('mydiv', Object.values(lines));
 
});
