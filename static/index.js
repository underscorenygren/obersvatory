function group_for_line_graph(datatable, x_axis_column_index, line_defining_index, value_defining_index) {
  /* Annoyingly, Google's line chart want's each row of a line graph
     to be the values of all lines and don't provide a convenient function
     to transpose, so we just do it here.
     If value_defining_index is null, will do counting instead*/

  var acc = {},
      distinct_values = datatable.getDistinctValues(line_defining_index),
      key_to_index = {}, result = new google.visualization.DataTable(), accumulated_keys,
      i, il, j, jl, key;

  result.addColumn('datetime', 'Date');
  for (i = 0, il = distinct_values.length; i < il; i++) {
    key = distinct_values[i];
    result.addColumn('number', key);
    key_to_index[key] = i + 1; //We add one to offset and not overwriting leading column
  }

  for (i = 0, il = datatable.getNumberOfRows(); i < il; i++) {

    var column_key = datatable.getValue(i, x_axis_column_index),
        line_defining_value = datatable.getValue(i, line_defining_index),
        existing = acc[column_key],
        column_value,
        previous,
        do_sum = value_defining_index === null;

    if (!do_sum) {
      column_value = datatable.getValue(i, value_defining_index);
    }

    if (!existing) {
      existing = new Array(distinct_values.length + 1).fill(0);
      existing[0] = column_key;
      acc[column_key] = existing;
    }

    if (do_sum) {
      previous = existing[key_to_index[line_defining_value]];
      if (previous) {
        column_value = previous + 1;
      } else {
        column_value = 1;
      }
    }
    existing[key_to_index[line_defining_value]] = column_value;
  }

  accumulated_keys = Object.keys(acc);
  for (i = 0, il = accumulated_keys.length; i < il; i++) {
    key = accumulated_keys[i];
    var row = acc[key];

    result.addRow(row);
  }

  return result;
}

function append_chart(data, constructor, opts) {
  opts = opts || {};
  var chart_name=opts.chart_name ||  Math.random().toString(36).substr(2, 5),
      default_insert = "#charts",
      insertion_point=opts.insertion_point || null,
      $insertion_point = jqFromStringOrObject(insertion_point, default_insert),
      chart_opts = opts.chart_opts || {},
      $chart = $("<div></div>").attr("id", chart_name),
      chart;

  console.log("drawing", data, "with", constructor, "as", name);

  $insertion_point.append($chart);
  chart = new constructor($chart[0]);
  chart.draw(data, chart_opts);

  return $chart;
}

function column_name_to_index(name, datatable) {
  for (var i = 0, il = datatable.getNumberOfColumns(); i < il; i++) {
    if (datatable.getColumnLabel(i) === name) {
      return i;
    }
  }
  return -1;
}

function toDate(datetime) {
  datetime.setHours(0);
  datetime.setMinutes(0);
  datetime.setSeconds(0);
  datetime.setMilliseconds(0);
  return datetime;
}

function jqFromStringOrObject(insertion_point, default_id) {
  if (!insertion_point) {
    insertion_point = default_id;
  }
  if (typeof insertion_point === "string") {
    var jqo = $(insertion_point);
    if (!jqo) {
      return null;
    }
    return jqo;
  } else {
    return insertion_point;
  }
}

function insert_toggled_table(datatable, options) {
  options = options || {};
  var $container = $("<div class='toggled-table'></div>"),
      chart_name = options.chart_name || null,
      insertion_point = options.insertion_point || "#charts",
      $etable, $toggle;
  jqFromStringOrObject(insertion_point, "#charts").append($container);
  $etable = append_chart(datatable,
      google.visualization.Table,
      { chart_name: chart_name,
        insertion_point: $container,
        chart_opts: {
          page: true,
          pageSize: 10}});
  $toggle = $("<a href='#'>Toggle</a>").click(function() {
      $etable.toggle();
      return false;
    });
  $toggle.insertBefore($etable);
  return $etable;
}


function serialize_control($control) {
  var schema = $control.find('._schema').text(),
      table = $control.find('._table').text(),
      inputs = $control.find('input'),
      type = $control.attr('data-type'),
      name = $control.find(".name").val(),
      serialized_inputs = {},
      i, il, input, $input;

  for (i = 0, il = inputs.length; i < il; i++) {
    input = inputs[i];
    $input = $(input);
    serialized_inputs[$input.attr('class')] = $input.val();
  }

  return {
    name: name,
    schema: schema,
    table: table,
    type: type,
    inputs: serialized_inputs
  };
}

function get_event_data(schema, table, days, callback) {
  var url = "/events/" + schema + "/" + table + "/";

  console.log("loading events from", url);
  $.getJSON(url, {"days": days}, callback);
}

function make_new_chart_from_data(serialized, days, $insert_at, callback) {
  var schema = serialized.schema,
      table = serialized.table,
      type = serialized.type,
      inputs = serialized.inputs;

  get_event_data(schema, table, days, function(data) {
    var $elem = make_new_chart(new google.visualization.DataTable(data),
        schema, table, type, inputs, $insert_at)();
    if (callback) {
      callback($elem);
    }
  });
}


function make_new_chart(datatable, schema, table, type, input_data, $insert_at) {
  $insert_at = $insert_at || $("#make_table");
  var $grouping, $trigger, html,
      click_fn;

  console.log("making chart of type", type, "at", $insert_at);

  switch(type) {
    case "pie":
      html = `
        <div class='controls'>
          Make New Graph From:
          <label class='_schema'></label>
          <label class='_table'></label>
          <label class='group'>Group By</label>
          <input class='group_input' type='text'/>
          <button class='submit' type='submit'>Render</button>
          <label>Name: </label>
          <input class='name' type="text" />
          <button class='save'>Save</button>
        </div>
        `;
      click_fn = make_pie_chart_click_fn(datatable, $insert_at);
      break;
    case "line":
    case "bar":
      html = `
        <div class='controls'>
          Make New Graph From:
          <label class='_schema'></label>
          <label class='_table'></label>
          <label class="x-axis"></label>
          <input class="x-axis-input" type="text" value="received_at"/>
          <label class='group'>Split Lines By</label>
          <input class='group_input' type='text'/>
          <label>Get Column Value</label>
          <input class='aggregate' type='text'/>
          <label>Aggregation Fn:</label>
          <input class='aggregation_fn_name' type='text' value="sum"/>
          <button class='submit' type='submit'>Render</button>
          <label>Name: </label>
          <input class='name' type="text" />
          <button class='save'>Save</button>
        </div>
        `;
      click_fn = make_line_or_bar_chart_click_fn(datatable, $insert_at, type === 'line');
      break;
    default:
        console.log("didn't recognize chart type", type);
        return;
  }

  $insert_at.empty();
  $insert_at.prepend(html);
  var $controls = $insert_at.find('.controls');
  $controls.attr('data-type', type);

  $controls.find('._schema').text(schema || "N/A");
  $controls.find('._table').text(table || "N/A");
  $trigger = $controls.find('.submit');
  if (input_data) {
    for (var key in input_data) {
      var value = input_data[key];
      $controls.find('input.' + key).val(value);
    }
  }

  $trigger.click(click_fn);
  $controls.find('button.save').click(function() {
    var data = JSON.stringify({'data': serialize_control($controls)}),
        name = $controls.find(".name").val();
    if (!name) {
      console.log("no name set for save");
    } else {
      $.post('/charts/' + name + "/", data,
          function() { console.log("wrote control"); }, 'json');
    }
  });

  return click_fn;

}

function make_line_or_bar_chart_click_fn(datatable, $insert_at, is_line) {
  return function() {
    var $grouping = $insert_at.find('.group_input'),
        split_by_name = $grouping.val(),
        split_by_index = column_name_to_index(split_by_name, datatable),
        x_axis_name = "received_at",
        x_axis_index = column_name_to_index(x_axis_name, datatable),
        constructor = is_line ? google.visualization.LineChart : google.visualization.BarChart,
        aggregation_name = $insert_at.find('.aggregate').val(),
        aggregation_fn_name = $insert_at.find('.aggregation_fn_name').val().toLowerCase(),
        selected_function = null,
        value_defining_index = null;

    if (x_axis_index === -1) {
      console.log("missing x_axis_index", x_axis_index, x_axis_name);
    } else {
      if (split_by_name && split_by_index === -1) {
        console.log("Couldn't find name to split by", split_by_name);
        return;
      }
      var aggregation_column = "uuid",
          google_aggr_fn = null,
          aggregation_index;

      if (aggregation_name) {
        value_defining_index = column_name_to_index(aggregation_name, datatable);
        if (value_defining_index === -1) {
          console.log("couldn't find aggregation column", aggregation_name);
          return;
        }
        aggregation_column = aggregation_name;
      } else {
        aggregation_fn_name = "count";
      }

      aggregation_index = column_name_to_index(aggregation_column, datatable);
      if (aggregation_index === -1) {
        console.log("couldn't find aggregation column", aggregation_index);
        return;
      }

      var grouped, $table_div = $("<div></div>"),
          fns = {
            "sum": google.visualization.data.sum,
            "count": google.visualization.data.count,
            "avg": google.visualization.data.avg,
            "min": google.visualization.data.min,
            "max": google.visualization.data.max,
          };

      if (split_by_name) {
        grouped = group_for_line_graph(datatable, x_axis_index, split_by_index, value_defining_index);
      } else {
        google_aggr_fn = fns[aggregation_fn_name];
        if (!google_aggr_fn) {
          console.log("couldn't find aggregation fn for", aggregation_fn_name);
          return;
        }
        grouped = google.visualization.data.group(datatable, [{
          "column": x_axis_index,
          "modifier": toDate,
          "type": "date"}],
          [{"column": aggregation_index,
            "label": aggregation_fn_name,
            "aggregation": google_aggr_fn,
            "type": "number"}
        ]);
      }
      $insert_at.append($table_div);
      insert_toggled_table(grouped, {insertion_point:$table_div});
      return append_chart(grouped, constructor, {insertion_point: $table_div});
    }
  };
}

function make_pie_chart_click_fn(datatable, $insert_at) {
  return function() {
    var $grouping = $insert_at.find('.group_input'),
        column_name = $grouping.val(),
        column_index = column_name_to_index(column_name, datatable),
        aggr_name = 'uuid',
        aggr_index = column_name_to_index(aggr_name, datatable),
        grouped_view;
    if (column_index === -1 || aggr_index === -1) {
      console.log("couldn't find column index for", column_name, aggr_name, column_index, aggr_index);
    } else {
      grouped_view = google.visualization.data.group(datatable,
        [column_index],
        [{"column": aggr_index, "aggregation": google.visualization.data.count, "type": "number"}]);
      var $table_div = $("<div></div>");
      $insert_at.append($table_div);
      return append_chart(grouped_view, google.visualization.PieChart,
          {insertion_point: $table_div});
    }
  };
}

function bind_chart_create(datatable) {
  var insertion_point = "#make_table",
      $insert = $(insertion_point),
      html = `
      <label>Make a New Chart</label>
      <div id="new_chart_btn" class="btn-group table-maker">
        <button>Line</button>
        <button>Pie</button>
        <button>Bar</button>
      </div>
      <div id="new_chart" class="table-maker">
      </div>`;
  $insert.empty();
  $insert.prepend(html);
  $insert.find('button').click(function() {
    make_new_chart(datatable, selected_schema, selected_table, $(this).text().toLowerCase());
  });
}

function onEnterKey($elem, callback) {
  $elem.on('keypress', function (e) {
    if(e.which === 13){
      callback(e, $elem);
    }
  });
}

function jqMake(tagname) {
  return $("<" + tagname + "></" + tagname + ">");
}

var init_days = (function() { //Sets the default value on first run, assign to callable fn
    var $days = $("#days"),
        DEFAULT_DAYS = 7;
    $days.val(DEFAULT_DAYS);
    return function() {
      return $days.val() || DEFAULT_DAYS;
    };
  }),

  loadCharts = function(callback) {
    google.charts.load('current', {'packages':['corechart', 'table', 'controls']});
    google.charts.setOnLoadCallback(function() {
      console.log("loaded gcharts");
      callback();
    });
  },

  _url = function(name, type) {
      return "./" + type + "/" + name + "/";
    };

