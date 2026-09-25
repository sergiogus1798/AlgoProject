# parameterCloud/model — what shape the cloud is, and who gives it that shape

| file | what it does | in → out |
|---|---|---|
| `space.py` | The level grid each parameter lives on, the unit cube, and which parameters still vary | panel → steps, unit, varying |
| `neighbourhood.py` | A1: the box around theta-zero, and its rank, plateau fraction and shrunk expectation | values → reading |
| `surrogate.py` | A3: the smooth model, its residual roughness, a model-free roughness, and the curvature | cloud → fit, curvature |
| `sensitivity.py` | A2: first-order and total Sobol indices, computed on the surrogate | fit → indices |

Decides nothing and reads no file.

**Why a quadratic and not a Gaussian process.** With k parameters it has 1 + 2k + k(k−1)/2
coefficients against thousands of points, it fits no hyperparameter on the same data it is judged
on, and its Hessian is exact rather than estimated — which is the number A3 actually wants. What it
gives up is prediction uncertainty, so it cannot say where the sampling is too sparse.

**Roughness is measured twice on purpose.** The residual kind (1 − r²) calls everything the
quadratic cannot represent noise, a real ridge included. `local_roughness` compares each tuple
against the median of its nearest neighbours and assumes no functional form at all. The word
"rough" is only used when both agree.

**A quadratic has one Hessian everywhere.** Fitted on the whole cloud it describes the global bowl;
fitted on the neighbourhood it describes the shape at theta-zero, which is the one the report
prints. The gradient is printed with it: a slope far from zero says the smooth optimum is not where
the strategy sits.
