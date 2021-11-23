"""
Add custom secondary sorting for the cluster view

The necessity of this plugin arises from the issue that the rows in the
cluster view are only sorted by one column without secondary ordering.
Within rows of identical value for that column, their order is arbitrary
and changes on splitting/merging actions. This tends to get confusing or
frustrating when dealing with large number of clusters.

Here, secondary sorting keys are implemented. They facilitate systematic
and deterministic ordering of rows with the same value in the primary
column. (The primary ordering column remains untouched: It is the
sorting that can be dynamically chosen by clicking the column headers,
as indicated by the ordering arrow, ▲ and ▼).

The list `column_order` contains the column identifiers by which to
order if two rows have identical values in the primary ordering column.
The list is prioritized: If the first element is equal for both rows,
the next column identifier in `column_order` will be checked. It is wise
to have 'id' as the last element, because it contains unique values. The
secondary orderings are always ascending, irrespective of whether the
primary column is set to ascending (▲) or descending (▼) ordering.

The variable `column_order` can be freely adjusted. However, the default
['ch', 'id'] seems to be optimal.
"""

import json
import logging
from phy import IPlugin, connect
from phy.cluster.supervisor import ClusterView

logger = logging.getLogger('phy')


class SortClusterView(IPlugin):
    def attach_to_controller(self, controller):

        # Priority of column sorting
        column_order = ['ch', 'id']

        # Javascript to execute
        js = """
          // Priority of column sorting
          var columnOrder = """ + json.dumps(column_order) + """;

          // Set a custom sort function
          table.sortFunction = function(itemA, itemB, options) {

            // Default sorting (see listjs)
            var sort = table.utils.naturalSort;
            sort.alphabet = table.alphabet || options.alphabet || undefined;
            if (!sort.alphabet && options.insensitive)
              sort = table.utils.naturalSort.caseInsensitive;

            // Primary and secondary keys
            var multi = 1;
            var keys = columnOrder.slice();
            keys.unshift(options.valueName);

            // Sort by the first non-identical column
            for (var i = 0; i < keys.length; i++) {
              if (itemA.values()[keys[i]] != itemB.values()[keys[i]])
                return sort(itemA.values()[keys[i]],
                            itemB.values()[keys[i]]) * multi;
              multi = options.order === 'desc' ? -1 : 1; // Always ascending
            }
          }

          // Resort now
          if(options.sort && options.sort[0])
            table.sort(options.sort[0], {"order": options.sort[1]});
        """

        @connect
        def on_gui_ready(sender, gui):
            view = gui.get_view(ClusterView)

            @connect(sender=view)
            def on_ready(sender):
                view.eval_js(js)
