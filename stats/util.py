def prepend(df, val):
    df.loc[-1] = val
    df.index = df.index + 1
    df = df.sort_index()
    return df
