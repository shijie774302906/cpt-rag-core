"""Synthetic fixed-method calculation, independent of any real site or source corpus."""
import json
import numpy as np
from cpt_core import fit_predict, local_calibration, reference_prior_center


def run():
    rng = np.random.default_rng(31415)
    qnet = np.array([260., 330., 390., 460., 530., 610., 680., 750.])
    # Artificial candidate predictions demonstrate the interface, not literature formulas.
    all_predictions = (qnet[:, None] / np.array([13., 17., 20.])[None, :]
                       * np.exp(rng.normal(0, .06, (len(qnet), 3))))
    references = np.array([19., 23., 31.])
    a, b = all_predictions[:3], all_predictions[3:]
    center = reference_prior_center(all_predictions, qnet, reference_factor=16.)
    zero = fit_predict(a, references, b)
    anchored = fit_predict(a, references, b, prior_center=center)
    local = local_calibration(qnet[:3], references, qnet[3:])
    def pack(result):
        return {key:np.asarray(result[key]).tolist() for key in ['median','pi95','weights']}
    return {'data_kind':'synthetic', 'unit':'kPa', 'target_count':len(b),
            'local_calibration':{'cone_factor':local['cone_factor'],'median':local['median'].tolist()},
            'calibrated_fusion':pack(zero), 'fusion_with_reference_prior':pack(anchored)}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2, allow_nan=False))
