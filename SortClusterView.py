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

Available: id, ch, sh, depth, fr, amp, n_spikes, comment, group, quality
"""

import json
import logging
from phy import IPlugin, connect
from phy.cluster.supervisor import ClusterView

logger = logging.getLogger('phy')


class SortClusterView(IPlugin):

    # Priority of column sorting
    column_order = ['ch', 'group', 'id']

    def attach_to_controller(self, controller):

        # Javascript to execute
        js_base = """
          // Priority of column sorting
          var columnOrder = """+json.dumps(SortClusterView.column_order)+""";

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
        """

        js_resort = """
          // Resort now
          if (options.sort && options.sort[0])
            table.sort(options.sort[0], {"order": options.sort[1]});
        """

        @connect
        def on_gui_ready(sender, gui):
            view = gui.get_view(ClusterView)

            @connect(sender=view)
            def on_ready(sender):
                view.eval_js(js_base)
                view.eval_js(js_resort)

            def prompt():
                return ','.join(SortClusterView.column_order)

            @controller.supervisor.actions.add(prompt=True,
                                               prompt_default=prompt,
                                               menu='Sele&ct',
                                               submenu='Sort by')
            def select_secondary_sorting(order):
                """
                Priority of secondary column ordering (comma-separated).
                Available: id, ch, sh, depth, fr, amp, n_spikes,
                comment, group, quality
                """
                column_avail = (['id'] + controller.supervisor.columns
                                + controller.supervisor.cluster_meta.fields)

                order = [c for c in order if c in column_avail]

                if len(order) > 0:
                    js_up = "columnOrder = " + json.dumps(order) + ";"
                    SortClusterView.column_order = order
                    view.eval_js(js_up)
                    view.eval_js(js_resort)
                    logger.info('Set secondary sorting to ' + ', '.join(order))
