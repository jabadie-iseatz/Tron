import logging
from tron.core import actionrun
from tron.core import action

log = logging.getLogger(__name__)


class ActionGraph(object):
    """A directed graph of actions and their requirements."""

    def __init__(self, graph, action_map):
        self.graph              = graph
        self.action_map         = action_map

    @classmethod
    def from_config(cls, actions_config, nodes, cleanup_action_config=None):
        """Create this graph from a job config."""
        actions = dict(
            (name, action.Action.from_config(conf, nodes))
            for name, conf in actions_config.iteritems()
        )
        if cleanup_action_config:
            cleanup_action = action.Action.from_config(
                    cleanup_action_config, nodes)
            actions[cleanup_action.name] = cleanup_action

        graph = cls._build_dag(actions, actions_config)
        return cls(graph, actions)

    @classmethod
    def _build_dag(cls, actions, actions_config):
        """Return a directed graph from a dict of actions keyed by name."""
        base = []
        for action in actions.itervalues():
            dependencies = actions_config[action.name].requires
            if not dependencies:
                base.append(action)
                continue

            for dependency in dependencies:
                dependency_action = actions[dependency]
                action.required_actions.append(dependency_action)
                dependency_action.dependent_actions.append(action)
        return base

    def actions_for_names(self, names):
        return (self.action_map[name] for name in names)


# TODO: this is a strange place for this class
class ActionRunFactory(object):
    """Construct ActionRuns and ActionRunCollections for a JobRun and
    ActionGraph.
    """

    @classmethod
    def build_action_run_collection(cls, job_run):
        """Create an ActionRunGraph from an ActionGraph and JobRun."""
        action_run_map = dict(
            (name, cls.build_run_for_action(job_run, action))
            for name, action in job_run.action_graph.action_map
        )
        return actionrun.ActionRunCollection(action_run_map)

    @classmethod
    def action_run_collection_from_state(cls, job_run, state_data):
        action_run_map = dict(
            (name, cls.action_run_from_state(job_run, state_data))
            for name, action in job_run.action_graph.action_map
        )
        return actionrun.ActionRunCollection(action_run_map)


#    @classmethod
#    def build_graph(cls, action_graph, action_run_map):
#        """Given an ActionGraph and a mapping of ActionRun.name to ActionRun
#        create a graph with the same structure as ActionGraph with the
#        ActionRun objects.
#        """
#        graph = []
#        action_map = action_graph.action_map
#
#        for name, action in action_map.iteritems():
#            action_run = action_run_map[name]
#            dependencies = action.required_actions
#            if not dependencies:
#                graph.append(action_run)
#                continue
#
#            for dependency in dependencies:
#                dependency_run = action_run_map[dependency.name]
#
#                action_run.required_actions.append(actions[dependency])
#        return base

    @classmethod
    def build_run_for_action(cls, action, job_run):
        """Create an ActionRun for a JobRun and Action."""
        id = "%s.%s" % (job_run.id, action.name)
        node = action.node_pool.next() if action.node_pool else job_run.node

        action_run = actionrun.ActionRun(
            id,
            node,
            job_run.run_time,
            action.command,
            parent_context=job_run.context,
            output_path=job_run.output_path,
            cleanup=action.is_cleanup
        )
        action_run.attach(True, job_run)
        return action_run

    @classmethod
    def action_run_from_state(cls, job_run, state_data):
        pass