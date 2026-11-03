import unittest
import numpy as np
from scipy.optimize import minimize
from cpt_core import fit_predict, niw_update, reference_prior_center, local_calibration
from cpt_core.solver import simplex_minimum
from cpt_core.scoring import score_component_evidence, PARENT_EQUAL_PROFILE
from cpt_core.metrics import prediction_metrics


class CoreTests(unittest.TestCase):
    def test_simplex_against_independent_optimizer(self):
        rng=np.random.default_rng(3)
        for m in (2,4,7):
            a=rng.normal(size=(m,m)); q=a@a.T+.1*np.eye(m)
            w,diagnostics=simplex_minimum(q)
            ref=minimize(lambda v:float(v@q@v),np.ones(m)/m,
                         jac=lambda v:2*q@v,bounds=[(0.,1.)]*m,
                         constraints={'type':'eq','fun':lambda v:v.sum()-1},
                         method='SLSQP',options={'ftol':1e-12,'maxiter':500})
            self.assertTrue(ref.success)
            self.assertAlmostEqual(float(w@q@w),float(ref.fun),places=8)
            self.assertLess(diagnostics['kkt_error'],1e-7)

    def test_reference_center_matches_mean_factor(self):
        q=np.array([200.,350.,500.]); f=np.array([[12.,15.],[20.,24.],[28.,32.]])
        c=reference_prior_center(f,q,16.)
        np.testing.assert_allclose(np.mean(q[:,None]/(f*np.exp(-c)),axis=0),16.)

    def test_one_reference_and_scale_equivariance(self):
        a=np.array([[20.,25.]]);y=np.array([22.]);b=np.array([[30.,35.],[40.,46.]])
        first=fit_predict(a,y,b);second=fit_predict(a*100,y*100,b*100)
        np.testing.assert_allclose(first['weights'],second['weights'],atol=1e-12)
        np.testing.assert_allclose(first['pi95']*100,second['pi95'],rtol=1e-12)
        self.assertTrue(np.all(first['pi95'][:,0]<first['median']))
        self.assertTrue(np.all(first['pi95'][:,1]>first['median']))

    def test_invalid_numeric_inputs(self):
        for bad in (np.array([[np.nan]]),np.array([[np.inf]])):
            with self.assertRaises(ValueError):niw_update(bad)
        with self.assertRaises(ValueError):fit_predict([[0.]],[1.],[[1.]])
        with self.assertRaises(ValueError):simplex_minimum([[1.,2.],[2.,1.]])

    def test_incompatible_evidence_not_combined(self):
        rubric={'query_id':'test','answer_pool':'provisional','groups':[
            {'group_id':'g','points':['p','q'],'evidence_options':[
                {'option_id':o,'components':{'p':[{'component_id':'p1','supports':[[x]]}],
                                            'q':[{'component_id':'q1','supports':[[y]]}]}}
                for o,x,y in [('a','a1','a2'),('b','b1','b2')]]}]}
        score=score_component_evidence(rubric,['a1','b2'],weight_profile=PARENT_EQUAL_PROFILE)
        self.assertEqual(score['reference_pool_coverage_percent'],50.)

    def test_local_factor_and_metrics(self):
        result=local_calibration([200.,400.],[10.,20.],[600.])
        self.assertAlmostEqual(result['cone_factor'],20.)
        np.testing.assert_allclose(result['median'],[30.])
        metrics=prediction_metrics([10.,20.],[10.,22.],[[8.,12.],[19.,23.]])
        self.assertAlmostEqual(metrics['mean_relative_absolute_error'],.05)
        self.assertEqual(metrics['coverage'],1.)


if __name__=='__main__':unittest.main()
