import logging
import subprocess
from tempfile import NamedTemporaryFile


model_params = {
    "powerlaw": ["phoindex"],
    "cutoff_powerlaw": ["phoindex", "cutoff", "efold"],
    "blackbody": ["kT"],
    "bremss": ["kT"],
    "plasma": ["kT", "abund"],
}


def _add_absorption(model_str, **kwargs):
    nh = kwargs.pop("nh", 1e19)
    model_str += f" {nh}"

    return model_str


def _add_redshift(model_str, **kwargs):
    z = kwargs.pop("z", None)
    if z:
        galnh = kwargs.pop("galnh", 1e19)
        model_str += f" z {z} {galnh}"

    return model_str


def _add_energy_range(cmd_str, key, elo=0.5, ehi=2, unabsorbed=False, **kwargs):
    elo, ehi = kwargs.pop(key, (elo, ehi))
    cmd_str += f" {elo}-{ehi}"

    if unabsorbed:
        cmd_str += " unabsorbed"

    return cmd_str


def _parse_model_args(model, **kwargs):
    # TODO: add multi-component models
    if model not in model_params:
        raise ValueError("Unknown model!")

    if model_params[model] is None:
        raise NotImplementedError

    if model == "cutoff_powerlaw":
        model_str = f"mo powerlaw"
    else:
        model_str = f"mo {model}"
    
    for param in model_params[model]:
        try:
            value = kwargs[param]
            model_str += f" {value}"

        except KeyError:
            raise ValueError(f"Parameter {param} missing for model {model}!")

    model_str = _add_absorption(model_str, **kwargs)
    model_str = _add_redshift(model_str, **kwargs)

    return model_str


def _parse_from_args(**kwargs):
    from_str = "from flux ergs"
    kwargs.pop("unabsorbed")
    return _add_energy_range(from_str, "input_energy_range", **kwargs)


def _parse_mission_args(**kwargs):
    mission = kwargs.pop("mission", None)
    unabsorbed = kwargs.pop("unabsorbed", False)

    if mission:
        unabsorbed = False
        mission_str = f"inst {mission}"
        
        for key in ["detector", "filter"]:
            try:
                value = kwargs[key]
                mission_str += f" {value}"

            except KeyError:
                raise ValueError(f"{key} missing for instrument {mission}!")
    else:
        mission_str = f"inst flux ergs"
    
    return _add_energy_range(
        mission_str, "output_energy_range", unabsorbed=unabsorbed, **kwargs
    )


def _make_script_file(file, *cmds):
    for cmd in cmds:
        file.write(cmd + "\n")

    file.seek(0)


def _run_pimms(filename):
    output = subprocess.check_output(["pimms", f"@{filename}"])
    logging.debug(output.decode())

    return output


def _parse_output(output):
    result = None
    for line in output.split(b"\n"):
        if line.startswith(b"* PIMMS predicts"):
            try:
                result = float(line.split()[3])
            
            except ValueError:
                result = float(line.split()[-2])

    return result


def pimms(flux, model="powerlaw", **kwargs):
    """
    Runs a PIMMS simulation.

    Parameters
    ----------
    flux : float
        Observed flux of the source in ergs/s/cm2.
    model : str, optional
        Spectral model. The available models are: "powerlaw", 
        "cutoff_powerlaw", "blackbody", "bremss" and "plasma",
        by default "powerlaw". See the PIMMS documentation for details
        on this models.
    input_energy_range : (float, float), optional
        Tuple (elo, ehi) defining the energy range (in keV) for the input flux 
        of the simulated source. By default (0.5, 2).
    output_energy_range : (float, float), optional
        Tuple (elo, ehi) defining the energy range (in keV) for the output 
        count rate of the simulated source. By default (0.5, 2).
    mission : str or None, optional
        Mission used for the simulation. The available missions are: "ASCA",
        "Athena", "BBXRT", "CGRO", "Chandra", "EINSTEIN", "EUVE", "EXOSAT",
        "Ginga", "HEAO1", "Hitomi", "Integral", "MAXI", "NICER", "NuSTAR", 
        "ROSAT", "SAX", "Suzaku", "Swift", "XMM" and "XTE". If None, then no
        spectral response is applied to the simulation and the output is the
        model flux (in ergs/s/cm-2) for the selected output energy range. By
        default is None.
    unabsorbed : bool, optional
        If True, the output flux wil be the intrinsic, absorption-corrected 
        value. This parameter is only taken into account if mission is None,
        otherwise the output value is always the absorbed count rate. By
        default is False.
    detector : str
        Detector used for the simulation. Mandatory if `mission` is not None.
        The actual accepted values depend on the selected mission. See the 
        PIMMS documentation for details.
    filter : str
        Filter used for the simulation. Mandatory if `mission` is not None.
        The actual accepted values depend on the selected mission and detector. 
        See the PIMMS documentation for details.

    Spectral model parameters
    ----------
    nh : float, optional
        Hydrogen column density in cm-2. All spectral models are modified by
        an absorption component. By default 1.0e19.
    phoindex : float, optional
        Photon index of the power law. Mandatory if `model` is "powerlaw" or
        "cutoff_powerlaw".
    cutoff : float, optional
        High energy cut-off in keV for a cut-off power law. Mandatory if `model`
        is "cutoff_powerlaw".
    efold : float, optional
        E-folding energy in keV for a cutoff power law. Mandatory if `model`
        is "cutoff_powerlaw".
    kT : float, optional
        Temperature in keV for thermal models. Mandatory if `model` is 
        "blackbody", "bremms" or "plasma".
    abund : float, optional
        Metal abundances of the plasma. Mandatory if `model` is "plasma".
    z : float or None, optional
        Redshift of the source. If z is None, the source spectrum is calculated
        at rest frame.
    galnh : float, optional
        Hydrogen column density in cm-2 for the Galactic absorption. If z is 
        not None, an additional absroption component is added into the spectral
        model to take into account the Galactic absorption. By default 1.0e19.

    Returns
    -------
    float
        Simulated count rate, or flux in ergs/s/cm-2 if `mission` is None.
    """
    cmd_list = (
        _parse_model_args(model, **kwargs),
        _parse_mission_args(**kwargs),
        _parse_from_args(**kwargs),
        f"go {flux}",
        "q",
    )
    with NamedTemporaryFile(mode="w", suffix=".xco") as file:
        _make_script_file(file, *cmd_list)
        output = _run_pimms(file.name)

    cr = _parse_output(output)

    return cr
