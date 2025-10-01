from django.db import models

# Create your models here.

class crop_price(models.Model):
    s_no = models.AutoField(primary_key=True)
    state=models.CharField(max_length=40,default='')
    city=models.CharField(max_length=40,default='')
    market_name=models.CharField(max_length=50,default='')
    commodity=models.CharField(max_length=40,default='')
    variety=models.CharField(max_length=40,default='Other')
    Grade=models.CharField(max_length=15,default='Local')
    min_Price = models.DecimalField(max_digits=12, decimal_places=4)
    max_Price = models.DecimalField(max_digits=12, decimal_places=4)
    modal_Price = models.DecimalField(max_digits=12, decimal_places=4)
    date=models.DateField()
