"""Artificial evidence identities illustrate the scoring arithmetic."""
import json
from cpt_core.scoring import score_component_evidence, PARENT_EQUAL_PROFILE


def run():
    rubric = {'query_id':'SYNTHETIC-01','answer_pool':'provisional','groups':[
        {'group_id':'method','points':['definition','condition'],'evidence_options':[
            {'option_id':'one_method','components':{
                'definition':[{'component_id':'definition.1','supports':[['e1']]}],
                'condition':[{'component_id':'condition.1','supports':[['e2']]},
                             {'component_id':'condition.2','supports':[['e3']]}]}}]}]}
    return score_component_evidence(rubric,['e1','e2'],weight_profile=PARENT_EQUAL_PROFILE)


if __name__ == '__main__':
    print(json.dumps(run(),indent=2))
