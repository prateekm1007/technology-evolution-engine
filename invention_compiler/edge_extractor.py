"""
Edge-extraction parser — Phase I of the Discovery Roadmap.

Per F-049: the current parser extracts keywords ('alloy', 'carbon')
from a Bi₂Te₃ paper, missing the actual material, mechanism, equations,
and manufacturing methods. This module replaces keyword extraction with
edge extraction: (source, target, direction, mechanism, evidence, tier).

The parser uses pattern-based extraction of mechanism-relevant phrases
from patent/paper text. It is NOT NLP — it is a structured regex
approach that identifies:
  1. Materials (chemical formulas, named compounds)
  2. Properties (measured quantities with units)
  3. Mechanisms (cause-effect relationships stated in text)
  4. Manufacturing methods (processing techniques)
  5. Performance metrics (quantitative results)

Each extracted entity becomes a node; each cause-effect relationship
becomes a CausalEdge tagged at the correct tier per DR-15.

This is the minimum viable mechanism extractor. It is not perfect —
it will miss some mechanisms and tag some as ASSERTED when they could
be DERIVED. But it will extract 'bismuth telluride,' 'Seebeck,'
'thermoelectric,' 'hot pressing,' and '2.51 W' — which is what the
Tellurium Test requires.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from invention_compiler.causal_graph import (
    CausalEdge, CausalNode, CausalGraph, EdgeTier, MechanismStatus,
    Intervention, Counterfactual,
)


class EdgeExtractor:
    """Extracts causal edges from patent/paper text.

    The extractor uses domain-specific patterns to identify:
    - Materials: chemical formulas (Bi2Te3, LiFePO4, etc.)
    - Properties: measured values with units (2.51 W, 3.58%, 120 K)
    - Mechanisms: cause-effect phrases ("enables," "produces," "achieves")
    - Manufacturing: processing methods (hot pressing, sintering, milling)
    - Performance: quantitative results (efficiency, power output)

    Each extraction produces a CausalNode and/or CausalEdge tagged at
    the appropriate tier per DR-15.
    """

    # Material patterns: chemical formulas and named compounds
    MATERIAL_PATTERNS = [
        (r'Bi2Te3|Bi₂Te₃|bismuth telluride', 'Bi2Te3', 'Bismuth telluride'),
        (r'Bi0\.46Sb1\.54Te3|Bi₀\.₄₆Sb₁\.₅₄Te₃', 'Bi0.46Sb1.54Te3', 'Bismuth antimony telluride'),
        (r'Bi2Te2\.7Se0\.3|Bi₂Te₂\.₇Se₀\.₃', 'Bi2Te2.7Se0.3', 'Bismuth telluride selenide'),
        (r'LiFePO4|LiFePO₄|lithium iron phosphate', 'LiFePO4', 'Lithium iron phosphate'),
        (r'LiPF6|LiPF₆', 'LiPF6', 'Lithium hexafluorophosphate'),
        (r'graphene oxide|GO membrane', 'graphene_oxide', 'Graphene oxide'),
        (r'BaSO4|BaSO₄|barium sulfate', 'BaSO4', 'Barium sulfate'),
        (r'PVDF|polyvinylidene fluoride', 'PVDF', 'Polyvinylidene fluoride'),
        (r'MOF|metal.organic framework', 'MOF', 'Metal-organic framework'),
        (r'garnet.*electrolyte|Li7La3Zr2O12|LLZO', 'LLZO', 'Garnet electrolyte (Li7La3Zr2O12)'),
        (r'tellurium|Te\b(?!st)', 'Te', 'Tellurium'),
        (r'bismuth|Bi\b', 'Bi', 'Bismuth'),
        # Sodium-ion battery materials (Apollo-II)
        (r'hard carbon|hard.carbon', 'hard_carbon', 'Hard carbon (Na-ion anode)'),
        (r'NaVPO4F|NaVPO₄F|sodium vanadium fluorophosphate', 'NaVPO4F', 'Sodium vanadium fluorophosphate'),
        (r'KVOPO4|KVOPO₄|potassium vanadium phosphate', 'KVOPO4', 'Potassium vanadium phosphate'),
        (r'Prussian blue|sodium.*hexacyanoferrate', 'prussian_blue', 'Prussian blue (Na cathode)'),
        (r'layered.*oxide.*sodium|Na.*layered.*oxide|P2.*type|O3.*type', 'layered_oxide_Na', 'Layered sodium oxide (P2/O3)'),
        (r'Na3V2.*PO4.*3|Na₃V₂.*PO₄.*₃|NVP', 'NVP', 'Sodium vanadium phosphate (Na3V2(PO4)3)'),
        (r'NaCrO2|NaCrO₂|sodium chromium oxide', 'NaCrO2', 'Sodium chromium oxide'),
        (r'biomass.*carbon|biomass.*hard.carbon', 'biomass_carbon', 'Biomass-derived hard carbon'),
        (r'Janus.*aminobenzene|aminobenzene.*anode', 'janus_aminobenzene', 'Janus aminobenzene anode'),
        (r'sodium|Na.ion', 'sodium', 'Sodium'),
        # Radiative cooling materials (Cycle 48 cross-domain corpus)
        (r'TiO2|TiO₂|titanium dioxide|titanium.?dioxide', 'TiO2', 'Titanium dioxide'),
        (r'PDMS|polydimethylsiloxane', 'PDMS', 'Polydimethylsiloxane'),
        (r'PVA|polyvinyl alcohol', 'PVA', 'Polyvinyl alcohol'),
        (r'PMMA|polymethyl methacrylate|acrylic', 'PMMA', 'Polymethyl methacrylate (acrylic)'),
        (r'calcium pyrophosphate|CPP ceramic', 'CPP_ceramic', 'Calcium pyrophosphate ceramic'),
        (r'calcium phosphate|Ca3.*PO4.*2|hydroxyapatite', 'calcium_phosphate', 'Calcium phosphate'),
        (r'silica microsphere|SiO2 microsphere|silica nanoparticle', 'silica_microsphere', 'Silica microsphere'),
        (r'alpha.quartz|α.quartz|α.SiO2', 'alpha_quartz', 'Alpha quartz (SiO2)'),
        (r'Li4Ti5O12|Li₄Ti₅O₁₂|lithium titanate', 'Li4Ti5O12', 'Lithium titanate (Li4Ti5O12)'),
        (r'β.SiC|beta.SiC|silicon carbide', 'SiC', 'Silicon carbide'),
        (r'glass.*polymer|polymer.*film.*cooling', 'glass_polymer_rc', 'Glass-polymer radiative cooling film'),
        # Phase 5 (cycle 63): expanded materials for 50x scaling
        (r'CO2|carbon dioxide', 'CO2', 'Carbon dioxide'),
        (r'Fe2O3|Fe₂O₃|iron oxide|hematite', 'Fe2O3', 'Iron oxide (Fe2O3)'),
        (r'TiO2|TiO₂|titanium dioxide', 'TiO2', 'Titanium dioxide'),  # already exists, keep
        (r'ZnO|zinc oxide', 'ZnO', 'Zinc oxide'),
        (r'CuO|copper oxide', 'CuO', 'Copper oxide'),
        (r'NiO|nickel oxide', 'NiO', 'Nickel oxide'),
        (r'Co3O4|cobalt oxide', 'Co3O4', 'Cobalt oxide'),
        (r'MnO2|manganese oxide', 'MnO2', 'Manganese oxide'),
        (r'WO3|tungsten oxide', 'WO3', 'Tungsten oxide'),
        (r'MoS2|molybdenum disulfide', 'MoS2', 'Molybdenum disulfide'),
        (r'WS2|tungsten disulfide', 'WS2', 'Tungsten disulfide'),
        (r'graphene\b|graphene.*sheet', 'graphene', 'Graphene'),
        (r'carbon nanotube|CNT\b', 'carbon_nanotube', 'Carbon nanotube'),
        (r'activated carbon|porous carbon', 'activated_carbon', 'Activated carbon'),
        (r'metal.organic framework|MOF\b', 'MOF', 'Metal-organic framework'),  # already exists, keep
        (r'zeolite|molecular sieve', 'zeolite', 'Zeolite'),
        (r'perovskite', 'perovskite', 'Perovskite'),
        (r'garnet.*electrolyte|Li7La3Zr2O12|LLZO', 'LLZO', 'Garnet electrolyte'),  # already exists, keep
        (r'Nafion|proton exchange membrane|PEM\b', 'Nafion', 'Nafion (PEM)'),
        (r'platinum|Pt\b(?!er)', 'Pt', 'Platinum'),
        (r'palladium|Pd\b', 'Pd', 'Palladium'),
        (r'ruthenium|Ru\b', 'Ru', 'Ruthenium'),
        (r'iridium|Ir\b', 'Ir', 'Iridium'),
        (r'cobalt|Co\b(?!mp)', 'Co', 'Cobalt'),
        (r'nickel|Ni\b', 'Ni', 'Nickel'),
        (r'copper|Cu\b(?!rve)', 'Cu', 'Copper'),
        (r'iron|Fe\b', 'Fe', 'Iron'),
        (r'platinum.*carbon|Pt.C\b', 'Pt_C', 'Platinum on carbon'),
        (r'Ag.*nanoparticle|silver.*nano', 'Ag_nano', 'Silver nanoparticles'),
        (r'Au.*nanoparticle|gold.*nano', 'Au_nano', 'Gold nanoparticles'),
        (r'LiCoO2|LCO\b|lithium cobalt oxide', 'LiCoO2', 'Lithium cobalt oxide (LCO)'),
        (r'LiMn2O4|LMO\b|lithium manganese oxide', 'LiMn2O4', 'Lithium manganese oxide (LMO)'),
        (r'NMC\b|LiNiMnCoO2', 'NMC', 'Nickel manganese cobalt oxide (NMC)'),
        (r'NCA\b|LiNiCoAlO2', 'NCA', 'Nickel cobalt aluminum oxide (NCA)'),
        (r'LFP\b|LiFePO4', 'LiFePO4', 'Lithium iron phosphate'),  # already exists, keep
        (r'Si.*anode|silicon.*anode', 'Si_anode', 'Silicon anode'),
        (r'Sn.*anode|tin.*anode', 'Sn_anode', 'Tin anode'),
        (r'Ge2Sb2Te5|GST\b|phase.change.*memory', 'GST', 'Ge2Sb2Te5 (phase-change)'),
        (r'BiFeO3|bismuth ferrite', 'BiFeO3', 'Bismuth ferrite'),
        (r'PbZrTiO3|PZT\b|lead zirconate titanate', 'PZT', 'Lead zirconate titanate'),
    ]

    # Property patterns: measured quantities
    PROPERTY_PATTERNS = [
        (r'(\d+\.?\d*)\s*W\b(?:.*power)', 'power_output', 'Power output', 'W'),
        (r'power output.*?(\d+\.?\d*)\s*W', 'power_output', 'Power output', 'W'),
        (r'efficiency.*?(\d+\.?\d*)\s*%', 'efficiency', 'Efficiency', '%'),
        (r'(\d+\.?\d*)\s*%\s*(?:efficiency|retention|yield)', 'efficiency', 'Efficiency', '%'),
        (r'(\d+\.?\d*)\s*(?:kWh/kg|kWh per kg)', 'specific_energy', 'Specific energy consumption', 'kWh/kg'),
        (r'temperature difference.*?(\d+)\s*K', 'temperature_difference', 'Temperature difference', 'K'),
        (r'(\d+)\s*K\b.*temperature', 'temperature', 'Temperature', 'K'),
        (r'Seebeck', 'seebeck_coefficient', 'Seebeck coefficient', 'V/K'),
        (r'ZT\b|figure of merit', 'figure_of_merit', 'Figure of merit (ZT)', 'dimensionless'),
        # Radiative cooling properties (cycle 48 cross-domain corpus)
        (r'cooling power.*?(\d+\.?\d*)\s*W/m2|cooling power.*?(\d+\.?\d*)\s*W.?m.?2',
         'cooling_power_density', 'Cooling power density', 'W/m2'),
        (r'(\d+\.?\d*)\s*W/m2.*cooling|cooling.*?(\d+\.?\d*)\s*W/m2',
         'cooling_power_density', 'Cooling power density', 'W/m2'),
        (r'(\d+\.?\d*)\s*W\s*/\s*m2', 'cooling_power_density', 'Cooling power density', 'W/m2'),
        (r'solar reflectance.*?(\d+\.?\d*)\s*%|(\d+\.?\d*)\s*%\s*solar reflect',
         'solar_reflectance', 'Solar reflectance', '%'),
        (r'emissivity.*?(\d+\.?\d*)|emittance.*?(\d+\.?\d*)',
         'infrared_emissivity', 'Infrared emissivity in sky window', 'dimensionless'),
        (r'sub.?ambient.*?(\d+\.?\d*)\s*(?:°|degrees?|C)|(\d+\.?\d*)\s*°?\s*C.*sub.?ambient',
         'subambient_temperature_drop', 'Sub-ambient temperature drop', 'C'),
        (r'(?:refractive index|index of refraction).*?(\d+\.?\d*)|(\d+\.?\d*)\s*refractive index',
         'refractive_index', 'Refractive index', 'dimensionless'),
        (r'band.?gap.*?(\d+\.?\d*)\s*eV|(\d+\.?\d*)\s*eV.*band.?gap',
         'bandgap', 'Electronic bandgap', 'eV'),
        # Phase 5 (cycle 63): expanded properties for 50x scaling
        (r'conductivity.*?(\d+\.?\d*)\s*S/cm|(\d+\.?\d*)\s*S/cm.*conductivity',
         'ionic_conductivity', 'Ionic conductivity', 'S/cm'),
        (r'capacity.*?(\d+\.?\d*)\s*mAh/g|(\d+\.?\d*)\s*mAh/g.*capacity',
         'specific_capacity', 'Specific capacity', 'mAh/g'),
        (r'voltage.*?(\d+\.?\d*)\s*V\b|(\d+\.?\d*)\s*V\b.*voltage',
         'voltage', 'Voltage', 'V'),
        (r'current density.*?(\d+\.?\d*)\s*mA/cm2',
         'current_density', 'Current density', 'mA/cm2'),
        (r'tensile strength.*?(\d+\.?\d*)\s*MPa',
         'tensile_strength', 'Tensile strength', 'MPa'),
        (r'thermal conductivity.*?(\d+\.?\d*)\s*W/m.?K',
         'thermal_conductivity', 'Thermal conductivity', 'W/mK'),
        (r'surface area.*?(\d+\.?\d*)\s*m2/g',
         'surface_area', 'Surface area', 'm2/g'),
        (r'cycling.*?retention.*?(\d+\.?\d*)\s*%',
         'cycling_retention', 'Cycling retention', '%'),
    ]

    # Mechanism patterns: cause-effect relationships
    MECHANISM_PATTERNS = [
        (r'(thermoelectric|TE)\s+(?:technology\s+)?(?:enables?|converts?|produces?)\s+(?:direct\s+)?heat.to.electricity',
         'thermoelectric', 'heat', 'electricity',
         'Thermoelectric effect converts heat to electricity via Seebeck coefficient'),
        (r'(?:heat.to.electricity|thermal.to.electric)\s+conversion',
         'thermoelectric_conversion', 'heat', 'electricity',
         'Thermoelectric conversion'),
        (r'(?:enables?|allows?|permits?)\s+(?:direct\s+)?heat.to.electricity',
         'thermoelectric', 'heat_gradient', 'electrical_power',
         'Temperature gradient produces electrical power via thermoelectric effect'),
        (r'radiative cooling|radiant cooling',
         'radiative_cooling', 'thermal_radiation', 'subambient_temperature',
         'Surface radiates heat to cold sky, achieving sub-ambient temperature'),
        (r'evaporative cooling',
         'evaporative_cooling', 'water_evaporation', 'temperature_reduction',
         'Water evaporation absorbs latent heat, reducing temperature'),
        (r'(?:phase.change|PCM)\s+(?:material|storage)',
         'pcm_storage', 'thermal_energy', 'stored_coolth',
         'Phase-change material stores thermal energy at melting point'),
        (r'(?:photorelectrochemical|PEC)\s+water\s+splitting',
         'pec_water_splitting', 'solar_photons', 'hydrogen',
         'Semiconductor photoanode absorbs photons, splits water into H2 and O2'),
        (r'(?:direct air capture|DAC)\s+(?:of\s+)?CO2',
         'dac_co2', 'amine_silica', 'captured_co2',
         'Amine-functionalized silica adsorbs CO2 from ambient air'),
        (r'(?:photoelectrochemical|PEC).*(?:water splitting|hydrogen)',
         'pec_water_splitting', 'solar_energy', 'hydrogen',
         'Photoelectrochemical water splitting'),
        (r'(?:nitrogen reduction|NRR).*(?:ammonia|NH3)',
         'nrr_catalysis', 'nitrogen', 'ammonia',
         'Catalytic reduction of N2 to NH3'),
        (r'(?:piezoelectric|piezo).*(?:energy harvesting|power)',
         'piezoelectric_harvesting', 'mechanical_strain', 'electrical_power',
         'Piezoelectric effect converts mechanical strain to electrical power'),
        (r'(?:biodegradable|biodegrad).*(?:polymer|plastic)',
         'biodegradation', 'biodegradable_polymer', 'decomposed_material',
         'Microbial/enzymatic breakdown of polymer chains'),
        # Sodium-ion battery mechanisms (Apollo-II)
        (r'sodium.*storage|Na.*storage.*mechanism|Na.ion.*intercalation',
         'na_storage', 'sodium_ions', 'stored_sodium',
         'Sodium ions intercalate into hard carbon structure during charging'),
        (r'sodium.*ion.*battery|Na.*ion.*battery|SIB',
         'sib_battery', 'sodium_ions', 'electrical_energy',
         'Sodium ions shuttle between cathode and anode, storing/releasing energy'),
        (r'layered.*oxide.*cathode|P2.*O3.*transition|phase.*transition.*cathode',
         'layered_oxide_transition', 'layered_oxide_Na', 'phase_transition',
         'Layered oxide cathode undergoes P2-O3 phase transition during cycling'),
        (r'electrochemical.*insertion|alkali.*metal.*insertion',
         'na_insertion', 'sodium_ions', 'intercalated_material',
         'Electrochemical insertion of sodium ions into electrode material'),
        # Radiative cooling mechanisms (cycle 48 cross-domain corpus)
        (r'atmospheric.*window|sky.*window.*(?:8|8-13|8 to 13).*(?:μm|um|micron)',
         'sky_window_emission', 'thermal_radiation', 'subambient_temperature',
         'Surface emits thermal radiation through 8-13 μm atmospheric window to cold sky'),
        (r'Restrahlen.*band|Reststrahlen.*band',
         'reststrahlen_emission', 'phonon_resonance', 'infrared_emissivity',
         'Phonon resonance in Reststrahlen bands produces high mid-IR emissivity'),
        (r'phonon resonance.*(?:9|8-13).*(?:μm|um|micron)|phonon.*mode.*infrared',
         'phonon_resonance_emission', 'phonon_resonance', 'infrared_emissivity',
         'Phonon resonance modes produce infrared emissivity in sky window'),
        (r'solar.*reflectance.*emissivity|reflect.*solar.*emit.*infrared',
         'pdrc_mechanism', 'solar_reflection', 'subambient_temperature',
         'PDRC reflects solar spectrum and emits thermal radiation through sky window'),
        (r'scattering.*solar|nanoparticle.*scattering.*reflect',
         'solar_scattering', 'nanoparticle', 'solar_reflection',
         'Nanoparticle scattering reflects solar spectrum'),
        (r'thermal.*radiation.*cold.*sky|emits.*heat.*sky',
         'sky_radiation_heat_sink', 'thermal_radiation', 'cold_sky',
         'Surface radiates heat to cold sky (3K space) as heat sink'),
        # Phase 5 (cycle 63): expanded mechanisms for 50x scaling
        (r'electrochemical.*water.*splitting|water.*splitting.*hydrogen',
         'ec_water_splitting', 'electrical_energy', 'hydrogen',
         'Electrochemical water splitting produces hydrogen'),
        (r'photocatalytic.*water.*splitting|photocatalysis.*hydrogen',
         'photocatalytic_splitting', 'solar_photons', 'hydrogen',
         'Photocatalytic water splitting produces hydrogen'),
        (r'intercalation.*sodium|Na.*intercalation|sodium.*intercalation',
         'na_intercalation', 'sodium_ions', 'intercalated_material',
         'Sodium ions intercalate into electrode material'),
        (r'redox.*reaction|oxidation.*reduction',
         'redox_reaction', 'chemical_reactants', 'electrical_energy',
         'Redox reaction converts chemical energy to electrical energy'),
        (r'adsorption.*desorption|sorbent.*capture',
         'adsorption_desorption', 'gas_molecules', 'captured_gas',
         'Adsorption-desorption cycle captures and releases gas'),
        (r'ion.*transport|ion.*conduction|ionic.*conduction',
         'ion_transport', 'ions', 'electrical_current',
         'Ion transport produces electrical current'),
        (r'photovoltaic.*effect|solar.*cell.*photovoltaic',
         'photovoltaic_effect', 'solar_photons', 'electrical_energy',
         'Photovoltaic effect converts solar photons to electricity'),
        (r'ferroelectric.*polarization|ferroelectric.*switching',
         'ferroelectric_polarization', 'electric_field', 'polarization_state',
         'Ferroelectric polarization switches under electric field'),
        (r'piezoelectric.*effect|piezoelectric.*strain',
         'piezoelectric_effect', 'mechanical_strain', 'electrical_charge',
         'Piezoelectric effect converts mechanical strain to electrical charge'),
    ]

    # Manufacturing method patterns
    MANUFACTURING_PATTERNS = [
        (r'hot pressing', 'hot_pressing', 'Hot pressing'),
        (r'spark.plasma sintering|SPS', 'spark_plasma_sintering', 'Spark-plasma sintering'),
        (r'ball milling', 'ball_milling', 'Ball milling'),
        (r'annealing.*?(\d+)\s*°?\s*C|annealing.*?(\d+)\s*degrees',
         'annealing', 'Annealing'),
        (r'tape casting', 'tape_casting', 'Tape casting'),
        (r'sol.gel', 'sol_gel', 'Sol-gel process'),
        (r'electrodeposition|electrochemical deposition',
         'electrodeposition', 'Electrodeposition'),
        (r'magnetron sputtering', 'magnetron_sputering', 'Magnetron sputtering'),
        (r'thermal evaporation', 'thermal_evaporation', 'Thermal evaporation'),
        # Sodium-ion battery manufacturing (Apollo-II)
        (r'biomass.*pyrolysis|pyrolysis.*biomass|carbonization.*biomass',
         'biomass_pyrolysis', 'Biomass pyrolysis (hard carbon synthesis)'),
        (r'ball.*milling.*sodium|milling.*Na',
         'na_ball_milling', 'Ball milling (Na-ion)'),
        # Radiative cooling manufacturing (cycle 48 cross-domain corpus)
        (r'spin.?coat|spin coating', 'spin_coating', 'Spin coating'),
        (r'dip.?coat|dip coating', 'dip_coating', 'Dip coating'),
        (r'spray.?coat|spray coating', 'spray_coating', 'Spray coating'),
        (r'roll.?to.?roll|roll to roll', 'roll_to_roll', 'Roll-to-roll coating'),
        (r'nano.*particle.*synth|nanoparticle.*preparation|co.?precipitation',
         'nanoparticle_synthesis', 'Nanoparticle synthesis (co-precipitation)'),
        (r'electrospinning|electro.?spin', 'electrospinning', 'Electrospinning'),
        (r'magnetron sputter.*multilayer|multilayer.*deposition',
         'multilayer_deposition', 'Multilayer deposition'),
    ]

    # Application patterns
    APPLICATION_PATTERNS = [
        (r'thermoelectric.*power generation|TE.*power',
         'te_power_generation', 'Thermoelectric power generation'),
        (r'radiative cooling|passive cooling',
         'passive_cooling', 'Passive radiative cooling'),
        (r'desalination|water purification',
         'desalination', 'Desalination'),
        (r'(?:battery|electrode|cathode|anode).*(?:lithium.ion|Li.ion)',
         'li_ion_battery', 'Lithium-ion battery'),
        (r'vertical farming',
         'vertical_farming', 'Vertical farming'),
        (r'water harvesting|atmospheric water',
         'water_harvesting', 'Atmospheric water harvesting'),
        (r'(?:direct air capture|DAC)',
         'co2_capture', 'Direct air capture of CO2'),
        (r'photoelectrochemical|water splitting.*hydrogen',
         'hydrogen_production', 'Solar hydrogen production'),
        (r'piezoelectric.*energy|energy harvesting.*piezo',
         'piezo_energy', 'Piezoelectric energy harvesting'),
        (r'biodegradable.*packaging|bioplastic',
         'biodegradable_packaging', 'Biodegradable packaging'),
        # Sodium-ion battery applications (Apollo-II)
        (r'sodium.*ion.*battery|Na.*ion.*battery|SIB',
         'sib_battery_app', 'Sodium-ion battery'),
        (r'grid.*storage|stationary.*storage|large.scale.*storage',
         'grid_storage', 'Grid-scale energy storage'),
        (r'low.cost.*battery|cheap.*battery|abundant.*sodium',
         'low_cost_battery', 'Low-cost battery (Na abundance)'),
        # Radiative cooling applications (cycle 48 cross-domain corpus)
        (r'passive daytime radiative cooling|PDRC',
         'pdrc_application', 'Passive daytime radiative cooling (PDRC)'),
        (r'building cooling|building.*thermal.*management|roof.*cooling',
         'building_cooling', 'Building cooling'),
        (r'solar cell cooling|photovoltaic.*cooling|PV.*cooling',
         'solar_cell_cooling', 'Solar cell / photovoltaic cooling'),
        (r'wearable cooling|wearable.*thermal',
         'wearable_cooling', 'Wearable cooling'),
        (r'automotive.*cooling|vehicle.*thermal.*management',
         'automotive_cooling', 'Automotive cooling'),
        (r'electronics cooling|electronics.*thermal.*management|chip.*cooling',
         'electronics_cooling', 'Electronics cooling'),
        (r'cold.*chain|refrigeration.*cold.*chain|vaccine.*cold.*chain',
         'cold_chain', 'Cold chain logistics'),
    ]

    # Direction patterns: INCREASES/DECREASES for Altshuller contradiction search
    # Expanded cycle 48: more patterns to catch contradictions
    DIRECTION_PATTERNS = [
        # "increases/enhances/improves X"
        (r'(?:increases?|enhances?|improves?|boosts?|raises?|elevates?|amplifies?|strengthens?)\s+(\w+)', 'increases'),
        # "decreases/reduces/lowers X"
        (r'(?:decreases?|reduces?|lowers?|diminishes?|degrades?|drops?|weakens?|suppresses?)\s+(\w+)', 'decreases'),
        # "X increases/enhances" (target before verb)
        (r'(\w+)\s+(?:increases?|enhances?|improves?|boosts?)', 'increases'),
        # "X decreases/reduces" (target before verb)
        (r'(\w+)\s+(?:decreases?|reduces?|lowers?|degrades?)', 'decreases'),
        # "higher X leads to higher Y" → X increases Y
        (r'higher\s+(\w+)\s+(?:leads? to|results? in|causes?)\s+higher\s+(\w+)', 'increases'),
        # "higher X leads to lower Y" → X decreases Y
        (r'higher\s+(\w+)\s+(?:leads? to|results? in|causes?)\s+lower\s+(\w+)', 'decreases'),
        # "X is enhanced by Y" → Y increases X
        (r'(\w+)\s+is\s+(?:enhanced|improved|increased)\s+by\s+(\w+)', 'increases'),
        # "X is reduced by Y" → Y decreases X
        (r'(\w+)\s+is\s+(?:reduced|degraded|decreased)\s+by\s+(\w+)', 'decreases'),
        # "achieves higher X" → increases X
        (r'achieves?\s+higher\s+(\w+)', 'increases'),
        # "achieves lower X" → decreases X
        (r'achieves?\s+lower\s+(\w+)', 'decreases'),
        # "limits/constrains X" → decreases X
        (r'(?:limits?|constrains?|restricts?|caps?)\s+(\w+)', 'decreases'),
        # "enables/allows X" → increases X (enabling = positive direction)
        (r'(?:enables?|allows?|permits?|facilitates?)\s+(?:higher\s+|increased\s+)?(\w+)', 'increases'),
        # "prevents/blocks X" → decreases X
        (r'(?:prevents?|blocks?|inhibits?|hinders?)\s+(\w+)', 'decreases'),
    ]


    # Intervention patterns: phrases that describe deliberate changes
    INTERVENTION_PATTERNS = [
        (r'(?:doping|doped|dopant).*(?:increases?|enhances?|improves?)\s+(\w+)',
         'doping', 'increase', 'Doping increases target parameter'),
        (r'(?:annealing|sintering).*(?:improves?|enhances?)\s+(\w+)',
         'annealing', 'increase', 'Annealing improves target parameter'),
        (r'(?:nanostructuring|nanostructure).*(?:enhances?|improves?)\s+(\w+)',
         'nanostructuring', 'increase', 'Nanostructuring enhances target parameter'),
        (r'(?:temperature|thermal).*(?:increases?|enhances?)\s+(\w+)',
         'temperature', 'increase', 'Temperature increases target parameter'),
        (r'(?:pressure|stress).*(?:increases?|decreases?)\s+(\w+)',
         'pressure', 'variable', 'Pressure changes target parameter'),
        (r'(?:concentration|loading).*(?:increases?|enhances?)\s+(\w+)',
         'concentration', 'increase', 'Concentration increases target parameter'),
    ]

    def __init__(self):
        self.compiled_materials = [(re.compile(p, re.IGNORECASE), nid, label)
                                    for p, nid, label in self.MATERIAL_PATTERNS]
        self.compiled_properties = [(re.compile(p, re.IGNORECASE), pid, plabel, unit)
                                     for p, pid, plabel, unit in self.PROPERTY_PATTERNS]
        self.compiled_mechanisms = [(re.compile(p, re.IGNORECASE), mid, src, tgt, mech)
                                     for p, mid, src, tgt, mech in self.MECHANISM_PATTERNS]
        self.compiled_manufacturing = [(re.compile(p, re.IGNORECASE), mid, mlabel)
                                        for p, mid, mlabel in self.MANUFACTURING_PATTERNS]
        self.compiled_applications = [(re.compile(p, re.IGNORECASE), aid, alabel)
                                        for p, aid, alabel in self.APPLICATION_PATTERNS]
        self.compiled_directions = [(re.compile(p, re.IGNORECASE), direction)
                                     for p, direction in self.DIRECTION_PATTERNS]
        self.compiled_interventions = [(re.compile(p, re.IGNORECASE), var, direction, desc)
                                        for p, var, direction, desc in self.INTERVENTION_PATTERNS]

    def extract(self, text: str, source_id: str, source_url: str = "",
                retrieval_date: str = "") -> CausalGraph:
        """Extract a causal graph from patent/paper text.

        Returns a CausalGraph with nodes and edges tagged at the
        appropriate tier per DR-15.

        Most edges will be ASSERTED (mechanism present in text but
        not evaluated against a formula). Some may be DERIVED if
        a formula is referenced. None will be OBSERVED unless the
        text explicitly states a measurement was performed.
        """
        graph = CausalGraph()
        provenance = {
            "source": source_id,
            "source_url": source_url,
            "retrieval_date": retrieval_date,
            "extracted_by": "EdgeExtractor",
        }
        now = datetime.now(timezone.utc).isoformat()

        # 1. Extract materials → nodes
        materials_found = []
        for pattern, node_id, label in self.compiled_materials:
            if pattern.search(text):
                node = CausalNode(
                    node_id=node_id, node_type="material", label=label,
                    properties={"source": source_id},
                    what_does_this_change=[],  # filled later
                    what_changes_this=[],
                    inputs=[], constraints=[], outputs=[],
                    evidence=[source_id],
                    provenance=provenance,
                )
                graph.add_node(node)
                materials_found.append((node_id, label))

        # 2. Extract properties → nodes + link to materials
        properties_found = []
        for pattern, prop_id, prop_label, unit in self.compiled_properties:
            m = pattern.search(text)
            if m:
                # Use the first non-None capture group; fall back to "present"
                value = None
                if m.groups():
                    for g in m.groups():
                        if g is not None:
                            value = g
                            break
                if value is None:
                    value = "present"
                node = CausalNode(
                    node_id=prop_id, node_type="property", label=prop_label,
                    properties={"value": value, "unit": unit, "source": source_id},
                    what_does_this_change=[],
                    what_changes_this=[],
                    inputs=[], constraints=[], outputs=[],
                    evidence=[source_id],
                    provenance=provenance,
                )
                graph.add_node(node)
                properties_found.append((prop_id, prop_label, value, unit))

                # Link each material to this property (ASSERTED edge)
                for mat_id, mat_label in materials_found:
                    edge = CausalEdge(
                        source=mat_id, target=prop_id, direction="causes",
                        mechanism=f"{mat_label} exhibits {prop_label}",
                        mechanism_status=MechanismStatus.ASSERTED,
                        evidence=[source_id], tier=EdgeTier.ASSERTED,
                        formula=None, formula_inputs=None, formula_output=None,
                        expected_output=float(value) if value.replace('.', '').isdigit() else None,
                        tolerance=None,
                        falsifiable_by=f"Measure {prop_label} of {mat_label}",
                        what_does_this_change=prop_label,
                        intervention=None, counterfactual=None,
                        created_at=now, provenance=provenance,
                    )
                    graph.add_edge(edge)

        # 3. Extract mechanisms → nodes + edges
        for pattern, mech_id, src_node, tgt_node, mechanism_desc in self.compiled_mechanisms:
            if pattern.search(text):
                # Add mechanism node
                mech_node = CausalNode(
                    node_id=mech_id, node_type="mechanism", label=mechanism_desc[:80],
                    properties={"description": mechanism_desc, "source": source_id},
                    what_does_this_change=[tgt_node],
                    what_changes_this=[src_node],
                    inputs=[src_node], constraints=[], outputs=[tgt_node],
                    evidence=[source_id],
                    provenance=provenance,
                )
                graph.add_node(mech_node)

                # Add causal edge (ASSERTED — mechanism described but not evaluated)
                edge = CausalEdge(
                    source=src_node, target=tgt_node, direction="causes",
                    mechanism=mechanism_desc,
                    mechanism_status=MechanismStatus.ASSERTED,
                    evidence=[source_id], tier=EdgeTier.ASSERTED,
                    formula=None, formula_inputs=None, formula_output=None,
                    expected_output=None, tolerance=None,
                    falsifiable_by=f"Test {mechanism_desc[:50]}",
                    what_does_this_change=tgt_node,
                    intervention=None, counterfactual=None,
                    created_at=now, provenance=provenance,
                )
                graph.add_edge(edge)

                # Link materials to this mechanism
                for mat_id, mat_label in materials_found:
                    edge = CausalEdge(
                        source=mat_id, target=mech_id, direction="enables",
                        mechanism=f"{mat_label} enables {mechanism_desc[:60]}",
                        mechanism_status=MechanismStatus.ASSERTED,
                        evidence=[source_id], tier=EdgeTier.ASSERTED,
                        formula=None, formula_inputs=None, formula_output=None,
                        expected_output=None, tolerance=None,
                        falsifiable_by=f"Test {mat_label} without {mech_id}",
                        what_does_this_change=mech_id,
                        intervention=None, counterfactual=None,
                        created_at=now, provenance=provenance,
                    )
                    graph.add_edge(edge)

        # 4. Extract manufacturing methods → nodes + link to materials
        for pattern, mfg_id, mfg_label in self.compiled_manufacturing:
            if pattern.search(text):
                node = CausalNode(
                    node_id=mfg_id, node_type="manufacturing", label=mfg_label,
                    properties={"source": source_id},
                    what_does_this_change=[f"material properties of {', '.join(m[0] for m in materials_found)}"],
                    what_changes_this=[],
                    inputs=[], constraints=[], outputs=[],
                    evidence=[source_id],
                    provenance=provenance,
                )
                graph.add_node(node)

                # Link manufacturing to materials (ASSERTED)
                for mat_id, mat_label in materials_found:
                    edge = CausalEdge(
                        source=mfg_id, target=mat_id, direction="produces",
                        mechanism=f"{mfg_label} produces {mat_label}",
                        mechanism_status=MechanismStatus.ASSERTED,
                        evidence=[source_id], tier=EdgeTier.ASSERTED,
                        formula=None, formula_inputs=None, formula_output=None,
                        expected_output=None, tolerance=None,
                        falsifiable_by=f"Produce {mat_label} via different method",
                        what_does_this_change=f"material properties of {mat_label}",
                        intervention=None, counterfactual=None,
                        created_at=now, provenance=provenance,
                    )
                    graph.add_edge(edge)

        # 5. Extract applications → nodes + link to mechanisms
        for pattern, app_id, app_label in self.compiled_applications:
            if pattern.search(text):
                node = CausalNode(
                    node_id=app_id, node_type="application", label=app_label,
                    properties={"source": source_id},
                    what_does_this_change=[],
                    what_changes_this=[],
                    inputs=[], constraints=[], outputs=[],
                    evidence=[source_id],
                    provenance=provenance,
                )
                graph.add_node(node)

                # Link mechanisms to applications
                for pattern2, mech_id, src, tgt, mech_desc in self.compiled_mechanisms:
                    if mech_id in [n.node_id for n in graph.nodes.values()]:
                        edge = CausalEdge(
                            source=mech_id, target=app_id, direction="enables",
                            mechanism=f"{mech_desc[:60]} enables {app_label}",
                            mechanism_status=MechanismStatus.ASSERTED,
                            evidence=[source_id], tier=EdgeTier.ASSERTED,
                            formula=None, formula_inputs=None, formula_output=None,
                            expected_output=None, tolerance=None,
                            falsifiable_by=f"Test {app_label} without {mech_id}",
                            what_does_this_change=app_label,
                            intervention=None, counterfactual=None,
                            created_at=now, provenance=provenance,
                        )
                        graph.add_edge(edge)

        # 6. Backfill what_does_this_change on material nodes
        # based on the edges that connect them
        for node_id, node in graph.nodes.items():
            if node.node_type == "material":
                changes = set(node.what_does_this_change)
                for edge in graph.edges:
                    if edge.source == node_id:
                        if edge.what_does_this_change:
                            changes.add(edge.what_does_this_change)
                node.what_does_this_change = list(changes)

        # 6. Extract direction metadata (INCREASES/DECREASES) for Altshuller
        direction_map = {}  # target_node → direction
        for pattern, direction in self.compiled_directions:
            for m in pattern.finditer(text):
                target = m.group(1).lower() if m.lastindex else None
                if target:
                    # Map the word to a known node ID
                    for nid in graph.nodes:
                        if target in nid.lower() or target in graph.nodes[nid].label.lower():
                            direction_map[nid] = direction

        # Annotate edges with direction
        for edge in graph.edges:
            if edge.target in direction_map:
                edge.direction = direction_map[edge.target]
            elif not hasattr(edge, 'direction') or edge.direction is None:
                # Keep the existing direction from the edge creation
                pass

        # 7. Extract interventions (Pearl test)
        from invention_compiler.causal_graph import Intervention
        for pattern, var, direction, desc in self.compiled_interventions:
            for m in pattern.finditer(text):
                target = m.group(1).lower() if m.lastindex else None
                if target:
                    # Map target to known nodes
                    for nid in graph.nodes:
                        if target in nid.lower() or target in graph.nodes[nid].label.lower():
                            # Create Intervention object on the edge from var to nid
                            for edge in graph.edges:
                                if edge.target == nid and not edge.intervention:
                                    edge.intervention = Intervention(
                                        node=var,
                                        intervention=f"change {var}",
                                        predicted_effect=f"{direction} {nid}",
                                        expected_magnitude="unknown",
                                        uncertainty="unknown",
                                    )
                                    break

        # 7. Create Intervention objects for Pearl test (DR-16/DR-23)
        # For edges where source is a material/manufacturing/property (something
        # you can change), create an Intervention: "change X → effect on Y"
        for edge in graph.edges:
            if edge.intervention is not None:
                continue  # already has intervention
            
            source_node = graph.nodes.get(edge.source)
            if source_node and source_node.node_type in ('material', 'manufacturing', 'property'):
                edge.intervention = Intervention(
                    node=edge.source,
                    intervention=f"change {edge.source}",
                    predicted_effect=f"change in {edge.target}",
                    expected_magnitude=None,
                    uncertainty=None,
                )

        return graph

    def extract_from_corpus(self, corpus_dir: str, use_discovery_graph: bool = True):
        """Extract from all files in a corpus directory (patents or papers).

        Merges all individual graphs into one combined graph.

        Per Law 28 (cycle 40): default is now use_discovery_graph=True
        (DiscoveryGraph is canonical). Set use_discovery_graph=False for
        backward compatibility with CausalGraph (thin wrapper).
        """
        import pathlib
        graph = CausalGraph()
        corpus = pathlib.Path(corpus_dir)

        for f in sorted(corpus.iterdir()):
            if not f.suffix == ".txt":
                continue
            content = f.read_text(encoding="utf-8")

            # Extract source metadata
            source_id = f.stem
            url_match = re.search(r'^URL:\s*(.+)$', content, re.MULTILINE)
            date_match = re.search(r'^RETRIEVAL DATE:\s*(.+)$', content, re.MULTILINE)
            source_url = url_match.group(1).strip() if url_match else ""
            retrieval_date = date_match.group(1).strip() if date_match else ""

            # Extract subgraph
            subgraph = self.extract(content, source_id, source_url, retrieval_date)

            # Merge into combined graph
            for nid, node in subgraph.nodes.items():
                if nid not in graph.nodes:
                    graph.add_node(node)
                else:
                    # Merge what_does_this_change lists
                    existing = graph.nodes[nid]
                    existing.what_does_this_change = list(
                        set(existing.what_does_this_change + node.what_does_this_change)
                    )
                    existing.evidence = list(set(existing.evidence + node.evidence))

            for edge in subgraph.edges:
                # Check if edge already exists (same source, target, mechanism)
                exists = any(
                    e.source == edge.source and e.target == edge.target
                    and e.mechanism == edge.mechanism
                    for e in graph.edges
                )
                if not exists:
                    graph.add_edge(edge)

        if use_discovery_graph:
            return graph.to_discovery_graph()
        return graph
