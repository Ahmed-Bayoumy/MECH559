%% HW2 --- Data-Based (Surrogate) Modeling
% Fill in the TODO sections below to answer each question in HW2.pdf.
% Each question is copied verbatim from HW2.pdf; write your discussion in the
% Dataset: aero_naca4_airfoil_panel.csv (NACA 4-digit airfoil, vortex-panel method, p=500)
% https://github.com/Ahmed-Bayoumy/MECH559/blob/DEV/Datasets/aero_naca4_airfoil_panel.csv
%
% Inputs (6): max_camber_m, camber_pos_p, thickness_t, alpha_deg, mach, reynolds
%             (use log10(reynolds) in place of the raw column)
% Output: CL
% "Scaled inputs" = per-column min-max scaling to [0,1] using TRAINING-set bounds.
%
% Requirements: base MATLAB + Statistics and Machine Learning Toolbox
% (fitrnet needs R2021a or newer).
%
% Rename this file <McGill_ID>_HW2.m before submitting (or "Save As" a Live Script,
% .mlx, if you prefer that format -- either way, use Publish to generate a PDF).

%% Setup: load and parse data
clear; clc; close all
SEED = 559;  % call rng(SEED) right before EVERY random step (cvpartition, fitrnet,
             % randperm) so your results do not depend on which cells you ran before

csvUrl = "https://raw.githubusercontent.com/Ahmed-Bayoumy/MECH559/DEV/Datasets/aero_naca4_airfoil_panel.csv";
T = readtable(csvUrl);

isTrain = strcmp(T.split, 'train');
isTest  = strcmp(T.split, 'test');
Ttrain = T(isTrain, :);
Ttest  = T(isTest, :);
fprintf('total=%d train=%d test=%d\n', height(T), height(Ttrain), height(Ttest));

rawCols = {'max_camber_m','camber_pos_p','thickness_t','alpha_deg','mach'};
featNames = [rawCols, {'log10_reynolds'}];

Xtr = [Ttrain{:, rawCols}, log10(Ttrain.reynolds)];
Xte = [Ttest{:, rawCols}, log10(Ttest.reynolds)];
ytr = Ttrain.CL;
yte = Ttest.CL;

rmseFn = @(y, yhat) sqrt(mean((y - yhat).^2));
r2Fn   = @(y, yhat) 1 - sum((y - yhat).^2) / sum((y - mean(y)).^2);

% One set of 5 CV folds, created once and reused in Q3, Q4 and Q5, so every
% model and every hyperparameter value is scored on the same folds.
rng(SEED);
cvp = cvpartition(size(Xtr,1), 'KFold', 5);

disp(['Xtr size: ', mat2str(size(Xtr)), '   Xte size: ', mat2str(size(Xte))])

%% Question 1 --- Design of experiments
% aero_naca4_airfoil_panel.csv was sampled with LHS (n=6, p=500), not a full-factorial
% grid. An LHS with p points has p distinct levels in every 1-D projection. Compute the
% full-factorial grid size needed to match this 1-D resolution (p^n runs) and compare it
% to p; conversely, find how many levels per dimension a grid of at most p runs can
% afford (floor(p^(1/n))). Briefly explain why LHS avoids this curse of dimensionality
% while still space-filling well in 1-D.

n = 6; p = 500;

% TODO: compute the full-factorial grid size needed to match p's 1-D resolution
% hint: gridFull = p ^ n;

% TODO: compute how many levels/dimension a budget of p runs can afford
% hint: levelsAfford = floor(p ^ (1/n));

% TODO: display both results and compare gridFull to p

%

%% Question 2 --- Polynomial regression from first principles
% Using the train rows, fit an affine model yhat(x;w) = w0 + sum_{j=1..6} wj*xj for CL
% (inputs: max_camber_m, camber_pos_p, thickness_t, alpha_deg, mach, log10(reynolds)) by
% solving the normal equations (Z^T Z) w = Z^T y directly -- adapt the Starter Code
% notebook's normal_equations_fit, or assemble Z yourself and pass Z^T Z and Z^T y to
% numpy.linalg.solve or MATLAB's backslash operator (no canned regression function; note
% that lstsq, or backslash applied to Z and y directly, does NOT form Z^T Z). Report w
% and the test RMSE/R^2, then confirm both match scikit-learn's LinearRegression (or
% MATLAB's fitlm).

% TODO: assemble the design matrix Z = [ones | Xtr] (intercept column + 6 raw inputs)
% hint: Ztr = [ones(size(Xtr,1),1), Xtr];
% hint: Zte = [ones(size(Xte,1),1), Xte];

% TODO: solve the normal equations directly -- do NOT call a regression function here
% hint: w = (Ztr' * Ztr) \ (Ztr' * ytr);

% TODO: predict on the test set and report RMSE/R^2
% hint: yhatTe = Zte * w;
% hint: fprintf('RMSE=%.6f  R2=%.6f\n', rmseFn(yte,yhatTe), r2Fn(yte,yhatTe));

% TODO: refit with fitlm and confirm it matches
% hint: mdl = fitlm(Xtr, ytr);
% hint: disp(mdl.Coefficients)

%

%% Question 3 --- Ill-conditioning and ridge regularization
% Extend question 2 to a pure quadratic (add w_{j+6}*xj^2, 13 columns in Z) and report
% kappa(Z^T Z). Min-max scale the inputs to [0,1] (training-set bounds), rebuild Z, and
% report the new condition number. Sweep the ridge penalty lambda in {0, 1e-4, 1e-2, 1,
% 100} (adapt ridge_fit, i.e. w_ridge = (Z^T Z + lambda*I)^(-1) Z^T y on the scaled Z;
% this penalizes w0 too, so if you use sklearn.linear_model.Ridge pass your own column of
% ones with fit_intercept=False to get the same result); using 5-fold CV on the training
% set, plot CV RMSE vs. lambda, report the best lambda, and compare its test RMSE/R^2 to
% lambda=0. Relate this to the bias-variance trade-off and to kappa(Z^T Z + lambda*I).

% TODO: build the pure-quadratic design matrix (intercept + 6 linear + 6 squared, 13 cols)
% hint: makeQuad = @(X) [X, X.^2];
% hint: ZtrQuadRaw = [ones(size(Xtr,1),1), makeQuad(Xtr)];

% TODO: report cond(Z'*Z) on the UNSCALED quadratic features
% hint: cond(ZtrQuadRaw' * ZtrQuadRaw)

% TODO: min-max scale the 6 inputs to [0,1] using TRAINING bounds, then rebuild quadratic Z
% hint: lo = min(Xtr); hi = max(Xtr);
% hint: scaleFn = @(X) (X - lo) ./ (hi - lo);
% hint: Xtr_s = scaleFn(Xtr); Xte_s = scaleFn(Xte);
% hint: ZtrQuad = [ones(size(Xtr_s,1),1), makeQuad(Xtr_s)];
% hint: ZteQuad = [ones(size(Xte_s,1),1), makeQuad(Xte_s)];

% TODO: report cond(Z'*Z) on the SCALED quadratic features and compare to the unscaled value

% TODO: sweep lambda in {0,1e-4,1e-2,1,100}; for each, run 5-fold CV on the training set
%       using the cvp folds created in Setup (do NOT create new folds per lambda)
% hint: lambdas = [0, 1e-4, 1e-2, 1, 100];
% hint: for iL = 1:numel(lambdas)
% hint:     lam = lambdas(iL);
% hint:     for k = 1:cvp.NumTestSets
% hint:         trIdx = training(cvp,k); vaIdx = test(cvp,k);
% hint:         Ztr_f = ZtrQuad(trIdx,:); ytr_f = ytr(trIdx);
% hint:         A = Ztr_f' * Ztr_f + lam * eye(size(Ztr_f,2));
% hint:         wRidge = A \ (Ztr_f' * ytr_f);
% hint:         foldRmse(k) = rmseFn(ytr(vaIdx), ZtrQuad(vaIdx,:) * wRidge);
% hint:     end
% hint:     cvRmse(iL) = mean(foldRmse);
% hint: end

% TODO: plot mean CV RMSE vs. lambda (semilogx), pick the best lambda
%       (lambda=0 cannot be shown on a log axis -- plot it at a small value and say so)

% TODO: fit on the full training set at lambda=0 and at the best lambda; compare test RMSE/R^2

%

%% Question 4 --- RBF and its spread parameter
% Fit a Gaussian RBF surrogate phi(r) = exp(-lambda*r^2) for CL (same 6 scaled inputs)
% with the Starter Code notebook (replace its 1-D distance by the Euclidean distance in
% 6-D) or a library, sweeping the spread over >=4 values across orders of magnitude
% (e.g. lambda in [1e-4, 1e3]; large lambda = narrow basis functions). If you use
% scipy.interpolate.RBFInterpolator, set kernel='gaussian' and epsilon = sqrt(lambda) --
% the default thin-plate kernel ignores epsilon; MATLAB's newrbe spread s corresponds to
% lambda = (0.8326/s)^2. Using 5-fold CV, plot CV RMSE vs. spread and identify the best
% value. Relate the too-narrow/too-wide extremes to the "good spread" vs. "poor spread"
% behavior from lecture.

% TODO: pick >= 4 spread values (lambda) spanning multiple orders of magnitude
% hint: spreads = [1e-3, 1e-2, 1e-1, 1, 10, 100];

% TODO: write an RBF fit/predict helper (Starter Code notebook's rbf_fit/rbf_predict,
%       with the 1-D distance replaced by the 6-D Euclidean distance, pdist2)
% hint: rbfFitPredict = @(Xa, ya, Xq, lam) ...
%           exp(-lam * pdist2(Xq, Xa).^2) * (exp(-lam * pdist2(Xa, Xa).^2) \ ya);
% note: for small lambda (wide kernels) MATLAB will warn that the matrix is close to
%       singular -- that is part of the answer; record cond(exp(-lam*pdist2(Xa,Xa).^2)).
% note: newrbe (Deep Learning Toolbox) is an optional alternative:
%       net = newrbe(Xa', ya', 0.8326/sqrt(lam)); yhat = net(Xq')';

% TODO: for each spread, run 5-fold CV with the cvp folds from Setup
% hint: yhat = rbfFitPredict(Xtr_s(trIdx,:), ytr(trIdx), Xtr_s(vaIdx,:), lam);

% TODO: plot mean CV RMSE vs. spread (loglog), identify the best spread

% TODO: fit on the full (scaled) training set at the best spread; report test RMSE/R^2

%

%% Question 5 --- Neural network width as a complexity knob
% Fit a single-hidden-layer network for CL (same 6 scaled inputs) with MLPRegressor (use
% solver='lbfgs', max_iter=5000, a fixed random_state; the default adam with 200
% iterations does not converge here) or fitrnet, sweeping the hidden-layer width over
% >=4 values (e.g. 2, 8, 32, 64). Using 5-fold CV, plot CV RMSE vs. width and identify
% where under- and overfitting set in.

% TODO: pick >= 4 widths, e.g. widths = [2, 8, 32, 64];

% TODO: for each width, run 5-fold CV (cvp folds from Setup) using fitrnet
%       (fitrnet uses L-BFGS; its defaults are 'relu' activation and Lambda=0)
% hint: rng(SEED);   % fixed initial weights, as random_state does in Python
% hint: mdl = fitrnet(Xtr_s(trIdx,:), ytr(trIdx), 'LayerSizes', width, ...
%                     'IterationLimit', 5000);
% hint: yhat = predict(mdl, Xtr_s(vaIdx,:));

% TODO: plot mean CV RMSE vs. width (semilogx)

% TODO: fit on the full training set at the best width; report test RMSE/R^2

%

%% Question 6 --- Kriging: correlation-matrix conditioning and uncertainty
% Draw a fixed random subsample of p=25 training points (e.g. np.random.default_rng(559))
% and use scaled inputs throughout this question. Using R(xi,xj) = exp(-theta*||xi-xj||^2)
% and the ordinary-Kriging equations from lecture
%   beta_hat = (1^T R^-1 1)^-1 1^T R^-1 y,
%   yhat(x_new) = beta_hat + r^T R^-1 (y - beta_hat*1),
% adapt the Starter Code notebook's Kriging fit/predict (not a black-box library) for this
% sub-step. For >=3 values of theta across orders of magnitude (e.g. 1e-3 to 1e2; call
% kriging_fit with nugget=0, since its default is 1e-10), report kappa(R) and comment on
% what a large value implies for computing R^-1; if R is (nearly) singular, apply a
% nugget R + eps*I (eps ~ 1e-6) and show it helps. Then fit Kriging on the FULL training
% set with a GP library (e.g. GaussianProcessRegressor with normalize_y=True and an
% anisotropic RBF(length_scale=np.ones(6)) kernel, or fitrgp with
% 'BasisFunction','constant'); report test RMSE/R^2 and the predicted std at the test
% points nearest to and farthest from the training set, and comment on how the
% uncertainty relates to distance from the training data.

% --- Part A: your own ordinary-Kriging predictor (small subsample) -----------------

% TODO: implement the correlation matrix R(xi,xj) = exp(-theta * ||xi-xj||^2)
% hint: corrMatrix = @(X1, X2, theta) exp(-theta * pdist2(X1, X2).^2);

% TODO: implement a krigingFit(X, y, theta, nugget) helper (struct with X, y, theta, Rinv, beta)
% hint: R = corrMatrix(X, X, theta) + nugget * eye(size(X,1));
% hint: Rinv = inv(R);
% hint: onesVec = ones(size(X,1),1);
% hint: beta = (onesVec' * Rinv * y) / (onesVec' * Rinv * onesVec);

% TODO: implement a krigingPredict(Xnew, model) helper -> yhat
% hint: r = corrMatrix(Xnew, model.X, model.theta);
% hint: yhat = model.beta + r * (model.Rinv * (model.y - model.beta));

% TODO: draw p=25 training points with a fixed seed
% hint: rng(SEED);
% hint: subIdx = randperm(size(Xtr_s,1), 25);

% TODO: for >= 3 theta values spanning orders of magnitude, report cond(R) (nugget=0)
% hint: cond(corrMatrix(Xsub, Xsub, theta))

% TODO: for the worst-conditioned theta, show that a nugget (R + 1e-6*I) helps

% --- Part B: full-scale fit with fitrgp ---------------------------------------------

% TODO: fit Kriging on the FULL scaled training set
% note: CL here is noise-free. By default fitrgp fits a noise level Sigma of at least
%       1e-2*std(y), which smooths the data and hides the distance effect you are asked
%       about -- so lower that bound and let the fitted noise level go small.
% hint: gprMdl = fitrgp(Xtr_s, ytr, 'BasisFunction','constant', ...
%                       'KernelFunction','ardsquaredexponential', ...
%                       'SigmaLowerBound',1e-6);
% hint: [yhatGp, ystdGp] = predict(gprMdl, Xte_s);

% TODO: report test RMSE/R^2

% TODO: find the nearest and farthest TEST point from the TRAINING set (scaled 6-D space)
% hint: D = pdist2(Xte_s, Xtr_s); minDist = min(D, [], 2);
% hint: [~, iNear] = min(minDist); [~, iFar] = max(minDist);

% TODO: report ystdGp at iNear and iFar, and comment on how uncertainty relates to distance

%

%% Bonus (optional, no penalty for skipping) --- Comparing surrogate families
% Collect your tuned models (CV-selected; Kriging by maximum likelihood) from questions
% 3-6 -- quadratic+ridge, RBF, ANN, Kriging -- into one table of test RMSE/R^2 for CL,
% each family's complexity knob, and whether it gives native uncertainty quantification
% (mirroring lecture's "Family / Complexity knob / Native UQ?" comparison). State which
% family you'd recommend and why, citing a property from the table.

% TODO: build a summary table with one row per family
% hint: family  = {'Polynomial (quad+ridge)'; 'RBF'; 'ANN'; 'Kriging/GP'};
% hint: knob    = {'lambda=...'; 'spread=...'; 'width=...'; 'theta (MLE)'};
% hint: testRMSE = [rmse1; rmse2; rmse3; rmse4];
% hint: testR2   = [r2_1; r2_2; r2_3; r2_4];
% hint: nativeUQ = {'No'; 'No'; 'No'; 'Yes (std)'};
% hint: resultsTable = table(family, knob, testRMSE, testR2, nativeUQ)

%
