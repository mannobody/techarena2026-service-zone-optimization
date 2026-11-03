"""Executable counterexamples and differential checks for the clustering report."""
import json
import time
import numpy as np
from scipy.optimize._numdiff import approx_derivative
from scipy.spatial.distance import pdist,squareform
from embeddings import HERE,Instance,Master,validator,affine_separable,road_profiles


def validate(data,sol):
    return validator.validate_solution(validator.Instance.model_validate(data),
                                      [validator.OpenedOffice.model_validate(r) for r in sol])


def main():
    start=time.perf_counter();rows={}
    data=dict(sites=[dict(x=1.,y=1.,reward=10.,tasks=[]),dict(x=1.,y=-1.,reward=10.,tasks=[])],
              offices=[dict(x=-1.,y=-1.,cost=0.,maxSize=1),dict(x=-1.,y=1.,cost=0.,maxSize=1)],
              workers=[],distances=[[0.,20.],[20.,0.]],maxDifference=0,balanceCoefficient=0.)
    sol=[dict(officeId=0,sites=[0],workers=[]),dict(officeId=1,sites=[1],workers=[])]
    assert validate(data,sol)==20.
    I=Instance(data);lp=affine_separable(I,np.array([0,1]));assert lp['affine_feasible'] is False
    exact=Master(I).solve(I.enumerate_columns(),integer=True,engine='scip',seconds=2.)
    assert abs(exact['value']-20.)<1e-7
    rows['crossing_allowed']=dict(point_packing_optimum=exact['value'],continuous_partition_upper_bound=10.,**lp)

    # Add an input point at the crossing, but do not serve it.
    bad=json.loads(json.dumps(data));bad['sites'].append(dict(x=0.,y=0.,reward=0.,tasks=[]))
    for r in bad['distances']:r.append(100.)
    assert validate(bad,sol)=='Hull conflict'
    embedded=json.loads(json.dumps(bad))
    for s,(x,y) in zip(embedded['sites'],[(-2.,1.),(2.,1.),(0.,3.)]):s.update(x=x,y=y)
    for o,(x,y) in zip(embedded['offices'],[(-2.,-1.),(2.,-1.)]):o.update(x=x,y=y)
    assert validate(embedded,sol)==20.
    rows['embedding_not_certificate']=dict(embedded_value=20.,original_error='Hull conflict',unserved_witness=2)

    rng=np.random.default_rng(63000);cost=rng.normal(size=(13,4));h=rng.normal(size=4)
    target=np.array([2.,3.,4.,4.]);tau=.7
    def fgh(x):
        z=(x-cost)/tau;mx=z.max(axis=1,keepdims=True);v=np.exp(z-mx);p=v/v.sum(axis=1,keepdims=True)
        f=float(tau*np.sum(mx[:,0]+np.log(v.sum(axis=1)))-target@x)
        g=p.sum(axis=0)-target
        H=(np.diag(p.sum(axis=0))-p.T@p)/tau
        return f,g,H
    f,g,H=fgh(h);fdg=approx_derivative(lambda x:fgh(x)[0],h,method='3-point').reshape(-1)
    fdH=approx_derivative(lambda x:fgh(x)[1],h,method='3-point')
    eg=float(np.max(np.abs(g-fdg)));eh=float(np.max(np.abs(H-fdH)))
    assert eg<1e-6 and eh<1e-6
    assert np.linalg.eigvalsh(H).min()>-1e-10 and np.max(np.abs(H@np.ones(4)))<1e-10
    rows['entropic_dual_derivatives']=dict(gradient_error=eg,hessian_error=eh,min_eigenvalue=float(np.linalg.eigvalsh(H).min()))
    # Atoms can split in a transport relaxation, but actual sites cannot.
    rows['atomic_target']=dict(sites=3,offices=2,target=[1.5,1.5],integer_equal_counts_feasible=False)
    # On the line, the own-office constraint keeps a two-cell boundary in [0,1].
    rows['anchored_mass_infeasible']=dict(offices=[0.,1.],sites=[10.,11.],boundary_interval=[0.,1.],
                                          target=[1,1],achievable_counts=[0,2])
    moved=json.loads(json.dumps(data));moved['distances']=(np.asarray(data['distances'])+np.array([7.,11.])).tolist()
    assert np.max(np.abs(road_profiles(Instance(data))-road_profiles(Instance(moved))))<1e-12
    rows['profile_shift_invariance']=True
    rows['different_balances']=dict(equal_site_counts=[2,2],task_loads=[2,10],task_range=8)
    # Even an ordinary L1 Voronoi cell need not be convex.
    centers=np.array([[0.,0.],[2.,1.]]);pair=np.array([[.4,10.],[1.4,.05]])
    probes=np.vstack((pair,pair.mean(axis=0)))
    labs=np.argmin(np.abs(probes[:,None,:]-centers[None,:,:]).sum(axis=2),axis=1)
    assert labs.tolist()==[0,0,1]
    rows['l1_nonconvex_cell']=dict(points=probes.tolist(),labels=labs.tolist())
    # Mixing arbitrary road costs into geometric costs breaks convexity for
    # every mixture with a nonzero road weight, even one very close to 0.
    mix=dict(sites=[dict(x=0.,y=-1.,reward=2.,tasks=[]),dict(x=0.,y=0.,reward=2.,tasks=[]),
                    dict(x=0.,y=1.,reward=2.,tasks=[])],
             offices=[dict(x=-1.,y=0.,cost=0.,maxSize=3),dict(x=1.,y=0.,cost=0.,maxSize=3)],
             workers=[],distances=[[0.,1.,0.],[1.,0.,1.]],maxDifference=3,balanceCoefficient=0.)
    mixed_sol=[dict(officeId=0,sites=[0,2],workers=[]),dict(officeId=1,sites=[1],workers=[])]
    assert validate(mix,mixed_sol)=='Hull conflict'
    rows['mixed_cost_nonconvex']=dict(road_label_pattern=[0,1,0],original_error='Hull conflict')
    for source in (data,bad):
        transformed=json.loads(json.dumps(source))
        for point in [*transformed['sites'],*transformed['offices']]:
            x,y=point['x'],point['y'];point.update(x=2*x+y+4,y=-x+3*y-2)
        assert validate(source,sol)==validate(transformed,sol)
    rows['invertible_affine_preserves_geometry']=True
    x=rng.normal(size=(20,5));centered=x-x.mean(axis=0)
    u,s,_=np.linalg.svd(centered,full_matrices=False);pca=u[:,:2]*s[:2]
    J=np.eye(20)-np.ones((20,20))/20;B=-.5*J@squareform(pdist(x))**2@J
    vals,vec=np.linalg.eigh(B);mds=vec[:,-2:]*np.sqrt(np.maximum(vals[-2:],0.))
    error=float(np.max(np.abs(pdist(pca)-pdist(mds))));assert error<1e-8
    rows['classical_mds_equals_profile_pca']=dict(distance_error=error)
    ranks=np.array([[0.,1.],[0.,100.]]);unit=ranks/np.linalg.norm(ranks,axis=1,keepdims=True)
    assert np.max(np.abs(unit[0]-unit[1]))<1e-12
    rows['unit_profile_loses_capacity_regret']=dict(costs=ranks.tolist(),normalized=unit.tolist(),
        balanced_assignment_costs=[1.,100.],lost_difference=99.)
    rows['seconds']=time.perf_counter()-start
    (HERE/'logs/theory_checks.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
