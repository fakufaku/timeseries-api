// First we extract any get request parameters
// that might be present from the URL
var url_string = window.location.href;
s = url_string.split('?');

if (s.length > 1) {
  get_params = '?' + s[1];
} else {
  get_params = '';
}

// Request the JSON data and plot
$.getJSON( "https://data.robinscheibler.org/api/series/21" + get_params, function( data ) {

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
