import numpy as np
import math

from welleng.utils import (
    MinCurve,
    get_nev,
    get_vec,
    get_angles,
    HLA_to_NEV,
    get_sigmas
)

from welleng.error import ErrorModel

class Survey:
    def __init__(
        self,
        md,
        inc,
        azi,
        n=None,
        e=None,
        tvd=None,
        x=None,
        y=None,
        z=None,
        vec=None,
        radius=None,
        cov_nev=None,
        cov_hla=None,
        # sigmaH=None,
        # sigmaL=None,
        # sigmaA=None,
        # sigmaN=None,
        # sigmaE=None,
        # sigmaV=None,
        error_model=None,
        well_ref_params=None,
        start_xyz=[0,0,0],
        start_nev=[0,0,0],
        deg=True,
        unit="meters"
    ):
        """
        Initialize a welleng.Survey object.

        Parameters
        ----------
            md: (,n) list or array of floats
                List or array of well bore measured depths.
            inc: (,n) list or array of floats
                List or array of well bore survey inclinations
            azi: (,n) list or array of floats
                List or array of well bore survey azimuths
        """
        self.unit = unit
        self.deg = deg
        self.start_xyz = start_xyz
        self.start_nev = start_nev
        self.md = np.array(md)
        self._make_angles(inc, azi, deg)
        self.radius = radius
        
        self.survey_deg = np.array([self.md, self.inc_deg, self.azi_deg]).T
        self.survey_rad = np.array([self.md, self.inc_rad, self.azi_rad]).T

        self.n = n
        self.e = e
        self.tvd = tvd
        self.x = x
        self.y = y
        self.z = z
        self.vec = vec

        self._min_curve()

        # initialize errors
        error_models = ["ISCWSA_MWD"]
        if error_model is not None:
            assert error_model in error_models, "Unrecognized error model"
        self.error_model = error_model
        self.well_ref_params = well_ref_params

        # self.sigmaH = sigmaH
        # self.sigmaL = sigmaL
        # self.sigmaA = sigmaA
        # self.sigmaN = sigmaN
        # self.sigmaE = sigmaE
        # self.sigmaV = sigmaV

        self.cov_hla = cov_hla
        self.cov_nev = cov_nev

        self._get_errors()

    def _min_curve(self):
        """

        """
        mc = MinCurve(self.md, self.inc_rad, self.azi_rad, self.start_xyz, self.unit)
        self.dogleg = mc.dogleg
        self.rf = mc.rf
        self.delta_md = mc.delta_md
        self.dls = mc.dls
        if self.x is None:
            self.x, self.y, self.z = mc.poss.T
        if self.n is None:
            self._get_nev()
        if self.vec is None:
            self.vec = get_vec(self.inc_rad, self.azi_rad, deg=False)

    def _get_nev(self):
        self.n, self.e, self.tvd = get_nev(
            np.array([
                self.x,
                self.y,
                self.z
            ]).T,
            self.start_xyz,
            self.start_nev
        ).T

    def _make_angles(self, inc, azi, deg=True):
        if deg:
            self.inc_rad = np.radians(inc)
            self.azi_rad = np.radians(azi)
            self.inc_deg = np.array(inc)
            self.azi_deg = np.array(azi)
        else:
            self.inc_rad = np.array(inc)
            self.azi_rad = np.array(azi)
            self.inc_deg = np.degrees(inc)
            self.azi_deg = np.degrees(azi)

    def _get_errors(self):
        if self.error_model:
            if self.error_model == "ISCWSA_MWD":
                self.err = ErrorModel(
                    survey=self.survey_deg,
                    surface_loc=self.start_xyz,
                    well_ref_params=self.well_ref_params,
                )
                # self.error_HLA = True
                self.cov_hla = self.err.cov_HLAs.T
                # self.sigmaH, self.sigmaL, self.sigmaA = get_sigmas(self.cov_hla)

                # self.error_NEV = True
                self.cov_nev = self.err.cov_NEVs.T
                # self.sigmaN, self.sigmaE, self.sigmaV = get_sigmas(self.cov_nev)

        # else:

        #     if (
        #         self.sigmaH is not None
        #         and self.sigmaL is not None
        #         and self.sigmaA is not None
        #     ):
        #         error_HLA = True
        #     else:
        #         error_HLA = False

        #     if (
        #         self.sigmaN is not None
        #         and self.sigmaE is not None
        #         and self.sigmaV is not None
        #     ):
        #         error_NEV = True
        #     else:
        #         error_NEV = False
            
        #     # if error_HLA and error_NEV:
        #     #     return
        #     if error_HLA:
        #         # self.error_HLA = make_cov(
        #         #     np.array(self.sigmaH),
        #         #     np.array(self.sigmaL),
        #         #     np.array(self.sigmaA),
        #         #     diag=True
        #         # )
        #         # self.error_NEV = HLA_to_NEV(self.survey_rad, self.error_HLA.T)
        #         # looks like there's some HLA error data but no NEV error data
        #         # make some error NEV data
        #         # print("Need to add the HLA_to_NEV function")
        #         self.cov_hla = make_cov(
        #             self.sigmaH,
        #             self.sigmaL,
        #             self.sigmaA,
        #             diag=True
        #         )
        #     else:
        #         self.cov_hla = None

        #     if error_NEV:
        #         # print("Need to add the NEV_to_HLA function")
        #         self.cov_nev = make_cov(
        #             self.sigmaN,
        #             self.sigmaE,
        #             self.sigmaV,
        #             diag=False
        #         )
        #     else:
        #         self.cov_nev = None

            # else:
            #     pass
            

def interpolate_survey(survey, x, index=0):
    """
    Interpolates a point distance x between two survey stations
    using minimum curvature.

    Parameters
    ----------
        survey: welleng.Survey
            A survey object with at least two survey stations.
        x: float
            Length along well path from indexed survey station to
            perform the interpolate at. Must be less than length
            to the next survey station.
        index: int
            The index of the survey station from which to interpolate
            from.

    Returns
    -------
        survey: welleng.Survey
            A survey object consisting of the two survey stations
            between which the interpolation has been made (index 0 and
            2), with the interpolated station between them (index 1)

    """
    index = int(index)

    assert index < len(survey.md) - 1, "Index is out of range"

    assert x <= survey.delta_md[index + 1], "x is out of range"


    # check if it's just a tangent section
    if survey.dogleg[index + 1] == 0:
        azi = survey.azi_rad[index]
        inc = survey.inc_rad[index]

    else:
        # get the vector
        t1 = survey.vec[index]
        t2 = survey.vec[index + 1]

        total_dogleg = survey.dogleg[index + 1]

        dogleg = x * (survey.dogleg[index + 1] / survey.delta_md[index + 1])

        t = (
            (math.sin(total_dogleg - dogleg) / math.sin(total_dogleg)) * t1
            + (math.sin(dogleg) / math.sin(total_dogleg)) * t2
        )

        inc, azi = get_angles(t)[0]

    s = Survey(
        md=np.array([survey.md[index], survey.md[index] + x]),
        inc=np.array([survey.inc_rad[index], inc]),
        azi=np.array([survey.azi_rad[index], azi]),
        start_xyz=np.array([survey.x, survey.y, survey.z]).T[index],
        start_nev=np.array([survey.n, survey.e, survey.tvd]).T[index],
        deg=False
    )
    s._min_curve()

    return s

def make_cov(a, b, c, diag=False):
    """
    Make a covariance matrix from the 1sigma errors.

    Parameters
    ----------
        a: (,n) list or array of floats
            Errors in H or N/y axis.
        b: (,n) list or array of floats
            Errors in L or E/x axis.
        c: (,n) list or array of floats
            Errors in A or V/TVD axis.
        diag: boolean (default=False)
            If true, only the lead diagnoal is calculated
            with zeros filling the remainder of the matrix.

    Returns
    -------
        cov: (n,3,3) np.array
    """

    if diag:
        z = np.zeros_like(np.array([a]).reshape(-1))
        cov = np.array([
            [a * a, z, z],
            [z, b * b, z],
            [z, z, c * c]
        ]).T
    else:
        cov = np.array([
            [a * a, a * b, a * c],
            [a * b, b * b, b * c],
            [a * c, b * c, c * c]
        ]).T

    return cov