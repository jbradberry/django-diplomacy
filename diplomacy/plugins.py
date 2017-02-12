from . import models
from .engine.main import actionable_subregions


class TurnGeneration(object):
    realm_types = {
        'diplomacygame': 'diplomacy.game',
    }

    agent_types = {
        'diplomacyempire': 'diplomacy.government',
    }

    permissions = {
        'turngeneration.add_generator': '_is_host',
        'turngeneration.change_generator': '_is_host',
        'turngeneration.delete_generator': '_is_host',
        'turngeneration.add_generationrule': '_is_host',
        'turngeneration.change_generationrule': '_is_host',
        'turngeneration.delete_generationrule': '_is_host',
        'turngeneration.add_pause': '_is_active_empire',
        'turngeneration.change_pause': '_is_active_empire',
        'turngeneration.delete_pause': '_is_active_empire',
        'turngeneration.add_ready': '_is_active_empire',
        'turngeneration.change_ready': '_is_active_empire',
        'turngeneration.delete_ready': '_is_active_empire',
    }

    def related_agents(self, realm, agent_type):
        if (agent_type.app_label, agent_type.model) == ('diplomacy', 'government'):
            return realm.government_set.all()

    def has_perm(self, user, perm, obj):
        methodname = self.permissions.get(perm)
        if methodname is None:
            return False
        return getattr(self, methodname, None)(user, obj)

    def _is_host(self, user, obj):
        return obj.owner == user

    def _is_active_empire(self, user, obj):
        turn = obj.current_turn()
        if not turn:
            return False
        empire = obj.government_set.filter(user=user)
        if not empire:
            return False
        return (
            any(o['government'] == empire.power and o['is_supply']
                for o in turn.get_ownership())
            or any(u['government'] == empire.power
                   for u in turn.get_units())
        )

    def is_ready(self, generator):
        turn = models.Turn.objects.filter(
            game_id=generator.object_id
        ).latest()
        units = turn.get_units()
        owns = turn.get_ownership()

        actors = actionable_subregions(turn.as_data(), units, owns)
        readys = set(r.agent.pk for r in generator.readies.all())
        return all(
            empire.pk in readys or not actors.get(empire.power)
            for empire in models.Government.objects.filter(
                game_id=generator.object_id,
            )
        )

    def auto_generate(self, realm):
        realm.generate()

    def force_generate(self, realm):
        realm.generate()
