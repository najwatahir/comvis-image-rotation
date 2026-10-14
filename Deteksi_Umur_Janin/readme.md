filename,pixel size(mm),head circumference (mm) -> 773_2HC.png,0.221600823932,292.20
docs : https://zenodo.org/records/1327317?preview_file=training_set.zip

Rumus umur janin dengan nilai HC only ->
log_GA_days = (
    0.05970 * (np.log(HC_mm)**2)
    +
    6.409e-9 * (HC_mm**3)
    +
    3.3258
)  

https://obgyn.onlinelibrary.wiley.com/doi/10.1002/uog.15894